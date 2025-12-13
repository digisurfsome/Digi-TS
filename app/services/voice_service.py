"""
Voice Service for Agent OS.

Provides voice input handling, Whisper transcription, timestamp tracking,
and tag management for Click-to-Rant and Real-Time Tagging features.
"""

import os
import time
import tempfile
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from openai import OpenAI

from app.services.process_log import ProcessLog


# ============================================================================
# VOICE RECORDING DATA STRUCTURES
# ============================================================================


class VoiceInputMode(str, Enum):
    """Mode of voice input."""
    CLICK_TO_RANT = "click_to_rant"  # Tap section, then speak
    REAL_TIME_TAG = "real_time_tag"  # Continuous rant with inline tagging


class RecordingState(str, Enum):
    """State of the recording."""
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"
    COMPLETE = "complete"
    ERROR = "error"


@dataclass
class TagEvent:
    """Represents a tag event during Real-Time Tagging."""
    section: str
    timestamp: float  # seconds from start
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": self.section,
            "timestamp": self.timestamp,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TagEvent":
        return cls(
            section=data["section"],
            timestamp=data["timestamp"],
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow()
        )


@dataclass
class TaggedSegment:
    """A segment of transcribed text with its associated tag."""
    section: str
    text: str
    start_time: float  # seconds
    end_time: float  # seconds

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section": self.section,
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaggedSegment":
        return cls(
            section=data["section"],
            text=data["text"],
            start_time=data["start_time"],
            end_time=data["end_time"]
        )


@dataclass
class VoiceRantData:
    """
    Complete voice rant data structure.

    Contains both raw transcript and organized tagged version.
    The raw transcript is SACRED and never modified.
    """
    raw_transcript: str
    total_duration: float  # seconds
    tags: List[TagEvent] = field(default_factory=list)
    segments: List[TaggedSegment] = field(default_factory=list)
    mode: VoiceInputMode = VoiceInputMode.REAL_TIME_TAG
    created_at: datetime = field(default_factory=datetime.utcnow)
    whisper_segments: Optional[List[Dict]] = None  # Raw Whisper API segments

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_transcript": self.raw_transcript,
            "total_duration": self.total_duration,
            "tags": [t.to_dict() for t in self.tags],
            "segments": [s.to_dict() for s in self.segments],
            "mode": self.mode.value,
            "created_at": self.created_at.isoformat(),
            "whisper_segments": self.whisper_segments
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoiceRantData":
        return cls(
            raw_transcript=data.get("raw_transcript", ""),
            total_duration=data.get("total_duration", 0),
            tags=[TagEvent.from_dict(t) for t in data.get("tags", [])],
            segments=[TaggedSegment.from_dict(s) for s in data.get("segments", [])],
            mode=VoiceInputMode(data.get("mode", "real_time_tag")),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            whisper_segments=data.get("whisper_segments")
        )

    def get_organized_dict(self) -> Dict[str, str]:
        """
        Get organized content by section.

        Returns:
            Dict mapping section name to concatenated text
        """
        organized = {}
        for segment in self.segments:
            if segment.section not in organized:
                organized[segment.section] = ""
            organized[segment.section] += segment.text + " "

        # Clean up whitespace
        return {k: v.strip() for k, v in organized.items()}


@dataclass
class RecordingSession:
    """
    Tracks an active recording session.

    Used for maintaining state during Click-to-Rant or Real-Time Tagging.
    """
    session_id: str
    mode: VoiceInputMode
    state: RecordingState = RecordingState.IDLE
    target_section: Optional[str] = None  # For Click-to-Rant mode
    start_time: Optional[datetime] = None
    tag_events: List[TagEvent] = field(default_factory=list)
    audio_chunks: List[bytes] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    def add_tag(self, section: str) -> TagEvent:
        """Add a tag event at the current timestamp."""
        tag = TagEvent(
            section=section,
            timestamp=self.elapsed_seconds
        )
        self.tag_events.append(tag)
        return tag

    def get_current_tag(self) -> Optional[str]:
        """Get the currently active tag section."""
        if not self.tag_events:
            return None
        return self.tag_events[-1].section

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "mode": self.mode.value,
            "state": self.state.value,
            "target_section": self.target_section,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "tag_events": [t.to_dict() for t in self.tag_events],
            "elapsed_seconds": self.elapsed_seconds
        }


# ============================================================================
# WHISPER TRANSCRIPTION
# ============================================================================


def transcribe_audio(
    audio_data: bytes,
    openai_api_key: str,
    model: str = "whisper-1",
    language: Optional[str] = None,
    response_format: str = "verbose_json"
) -> Tuple[str, List[Dict], float]:
    """
    Transcribe audio using OpenAI Whisper API.

    Args:
        audio_data: Audio bytes (supports mp3, mp4, m4a, wav, webm)
        openai_api_key: OpenAI API key
        model: Whisper model to use (default: whisper-1)
        language: Optional language hint (e.g., "en")
        response_format: Response format (verbose_json gives timestamps)

    Returns:
        Tuple of (full_text, segments_list, duration_seconds)
    """
    if not openai_api_key:
        ProcessLog.error("VoiceService", "No OpenAI API key for transcription")
        raise ValueError("OpenAI API key required for transcription")

    if not audio_data or len(audio_data) == 0:
        ProcessLog.warning("VoiceService", "Empty audio data provided")
        return "", [], 0.0

    ProcessLog.info("VoiceService", f"Transcribing audio ({len(audio_data)} bytes)")
    start_time = time.time()

    try:
        client = OpenAI(api_key=openai_api_key)

        # Write audio to temporary file (Whisper API requires file)
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_file:
            tmp_file.write(audio_data)
            tmp_path = tmp_file.name

        try:
            # Call Whisper API
            with open(tmp_path, "rb") as audio_file:
                kwargs = {
                    "model": model,
                    "file": audio_file,
                    "response_format": response_format
                }
                if language:
                    kwargs["language"] = language

                response = client.audio.transcriptions.create(**kwargs)

            # Parse response based on format
            if response_format == "verbose_json":
                full_text = response.text
                segments = []
                duration = response.duration if hasattr(response, 'duration') else 0.0

                if hasattr(response, 'segments'):
                    for seg in response.segments:
                        segments.append({
                            "start": seg.get("start", seg.start) if isinstance(seg, dict) else seg.start,
                            "end": seg.get("end", seg.end) if isinstance(seg, dict) else seg.end,
                            "text": seg.get("text", seg.text) if isinstance(seg, dict) else seg.text
                        })
            else:
                full_text = response if isinstance(response, str) else response.text
                segments = []
                duration = 0.0

            duration_ms = (time.time() - start_time) * 1000

            ProcessLog.success(
                "VoiceService",
                f"Transcription complete: {len(full_text)} chars, {len(segments)} segments",
                details={"duration": duration, "segments": len(segments)},
                duration_ms=duration_ms
            )

            return full_text, segments, duration

        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    except Exception as e:
        ProcessLog.error("VoiceService", f"Transcription failed: {str(e)}")
        raise


def transcribe_audio_file(
    file_path: str,
    openai_api_key: str,
    model: str = "whisper-1",
    language: Optional[str] = None
) -> Tuple[str, List[Dict], float]:
    """
    Transcribe audio from a file path.

    Args:
        file_path: Path to audio file
        openai_api_key: OpenAI API key
        model: Whisper model to use
        language: Optional language hint

    Returns:
        Tuple of (full_text, segments_list, duration_seconds)
    """
    with open(file_path, "rb") as f:
        audio_data = f.read()

    return transcribe_audio(audio_data, openai_api_key, model, language)


# ============================================================================
# TIMESTAMP-BASED TEXT SPLITTING
# ============================================================================


def split_transcript_by_tags(
    full_transcript: str,
    whisper_segments: List[Dict],
    tag_events: List[TagEvent],
    total_duration: float
) -> List[TaggedSegment]:
    """
    Split transcribed text by tag timestamps.

    Uses Whisper's word-level or segment-level timestamps to accurately
    split the transcript based on when tags were tapped.

    Args:
        full_transcript: Complete transcribed text
        whisper_segments: Whisper API segments with timestamps
        tag_events: List of tag events with timestamps
        total_duration: Total duration of recording

    Returns:
        List of TaggedSegment objects
    """
    if not tag_events:
        # No tags - return everything as one untagged segment
        return [TaggedSegment(
            section="Untagged",
            text=full_transcript,
            start_time=0.0,
            end_time=total_duration
        )]

    if not whisper_segments:
        # No segments - do simple proportional split
        return _split_proportionally(full_transcript, tag_events, total_duration)

    # Sort tag events by timestamp
    sorted_tags = sorted(tag_events, key=lambda t: t.timestamp)

    # Create time ranges for each tag
    tag_ranges = []
    for i, tag in enumerate(sorted_tags):
        start = tag.timestamp
        end = sorted_tags[i + 1].timestamp if i + 1 < len(sorted_tags) else total_duration
        tag_ranges.append((tag.section, start, end))

    # Assign whisper segments to tag ranges
    tagged_segments = []

    for section, range_start, range_end in tag_ranges:
        segment_texts = []

        for seg in whisper_segments:
            seg_start = seg.get("start", 0)
            seg_end = seg.get("end", 0)
            seg_text = seg.get("text", "")

            # Check if segment overlaps with tag range
            # Use midpoint to determine assignment
            seg_mid = (seg_start + seg_end) / 2

            if range_start <= seg_mid < range_end:
                segment_texts.append(seg_text)

        if segment_texts:
            tagged_segments.append(TaggedSegment(
                section=section,
                text=" ".join(segment_texts).strip(),
                start_time=range_start,
                end_time=range_end
            ))

    return tagged_segments


def _split_proportionally(
    full_transcript: str,
    tag_events: List[TagEvent],
    total_duration: float
) -> List[TaggedSegment]:
    """
    Split transcript proportionally when no word timestamps available.

    Uses character count proportional to time duration.
    """
    if not tag_events or total_duration == 0:
        return [TaggedSegment(
            section="Untagged",
            text=full_transcript,
            start_time=0.0,
            end_time=total_duration
        )]

    sorted_tags = sorted(tag_events, key=lambda t: t.timestamp)
    total_chars = len(full_transcript)

    segments = []
    current_char = 0

    for i, tag in enumerate(sorted_tags):
        start_time = tag.timestamp
        end_time = sorted_tags[i + 1].timestamp if i + 1 < len(sorted_tags) else total_duration

        # Calculate character range based on time proportion
        start_char = int((start_time / total_duration) * total_chars) if total_duration > 0 else 0
        end_char = int((end_time / total_duration) * total_chars) if total_duration > 0 else total_chars

        text = full_transcript[start_char:end_char].strip()

        if text:
            segments.append(TaggedSegment(
                section=tag.section,
                text=text,
                start_time=start_time,
                end_time=end_time
            ))

    return segments


# ============================================================================
# CLICK-TO-RANT FUNCTIONALITY
# ============================================================================


def process_click_to_rant(
    audio_data: bytes,
    target_section: str,
    openai_api_key: str
) -> Tuple[str, str]:
    """
    Process a Click-to-Rant recording.

    In Click-to-Rant mode, the user clicks a section label, speaks,
    and all transcribed text goes to that section.

    Args:
        audio_data: Recorded audio bytes
        target_section: The section being filled
        openai_api_key: OpenAI API key

    Returns:
        Tuple of (transcribed_text, target_section)
    """
    ProcessLog.info("VoiceService", f"Processing Click-to-Rant for section: {target_section}")

    text, segments, duration = transcribe_audio(audio_data, openai_api_key)

    ProcessLog.success(
        "VoiceService",
        f"Click-to-Rant complete: {len(text)} chars for {target_section}",
        details={"section": target_section, "duration": duration}
    )

    return text, target_section


# ============================================================================
# REAL-TIME TAGGING FUNCTIONALITY
# ============================================================================


def process_real_time_rant(
    audio_data: bytes,
    tag_events: List[TagEvent],
    openai_api_key: str
) -> VoiceRantData:
    """
    Process a Real-Time Tagging recording.

    In Real-Time Tagging mode, the user speaks continuously and taps
    tag buttons to mark sections as they go.

    Args:
        audio_data: Recorded audio bytes
        tag_events: List of tag events with timestamps
        openai_api_key: OpenAI API key

    Returns:
        VoiceRantData with both raw and organized content
    """
    ProcessLog.info("VoiceService", f"Processing Real-Time Tagging with {len(tag_events)} tags")

    # Transcribe the audio
    full_text, whisper_segments, duration = transcribe_audio(audio_data, openai_api_key)

    # Split by tags
    tagged_segments = split_transcript_by_tags(
        full_text,
        whisper_segments,
        tag_events,
        duration
    )

    # Build VoiceRantData
    rant_data = VoiceRantData(
        raw_transcript=full_text,
        total_duration=duration,
        tags=tag_events,
        segments=tagged_segments,
        mode=VoiceInputMode.REAL_TIME_TAG,
        whisper_segments=whisper_segments
    )

    ProcessLog.success(
        "VoiceService",
        f"Real-Time Tagging complete: {len(full_text)} chars, {len(tagged_segments)} segments",
        details={
            "duration": duration,
            "tags": len(tag_events),
            "segments": len(tagged_segments)
        }
    )

    return rant_data


# ============================================================================
# SESSION STATE HELPERS
# ============================================================================


def create_recording_session(
    mode: VoiceInputMode,
    target_section: Optional[str] = None
) -> RecordingSession:
    """
    Create a new recording session.

    Args:
        mode: Voice input mode
        target_section: Target section for Click-to-Rant mode

    Returns:
        New RecordingSession
    """
    import uuid

    session = RecordingSession(
        session_id=str(uuid.uuid4()),
        mode=mode,
        state=RecordingState.IDLE,
        target_section=target_section
    )

    ProcessLog.info("VoiceService", f"Created recording session: {session.session_id}")
    return session


def start_recording(session: RecordingSession) -> RecordingSession:
    """Mark a recording session as started."""
    session.state = RecordingState.RECORDING
    session.start_time = datetime.utcnow()
    ProcessLog.info("VoiceService", f"Recording started: {session.session_id}")
    return session


def stop_recording(session: RecordingSession) -> RecordingSession:
    """Mark a recording session as stopped."""
    if session.start_time:
        elapsed = (datetime.utcnow() - session.start_time).total_seconds()
        session.elapsed_seconds = elapsed
    session.state = RecordingState.PROCESSING
    ProcessLog.info("VoiceService", f"Recording stopped: {session.session_id}, {session.elapsed_seconds:.1f}s")
    return session


# ============================================================================
# AGENT OS SECTION MAPPING
# ============================================================================


# Map display names to Agent OS section keys
SECTION_DISPLAY_MAP = {
    "Overview": "overview",
    "Requirements (Functional)": "requirements_functional",
    "Requirements (Technical)": "requirements_technical",
    "User Stories": "user_stories",
    "Acceptance Criteria": "acceptance_criteria",
    "Technical Specification": "technical_spec",
    "Success Metrics": "success_metrics",
    "Questions": "questions",
    # Shorter versions for UI
    "Functional Req": "requirements_functional",
    "Technical Req": "requirements_technical",
    "Tech Spec": "technical_spec",
    "Metrics": "success_metrics",
}


def get_section_key(display_name: str) -> str:
    """
    Convert display name to Agent OS section key.

    Args:
        display_name: User-facing section name

    Returns:
        Internal section key
    """
    return SECTION_DISPLAY_MAP.get(display_name, display_name.lower().replace(" ", "_"))


def get_taggable_sections() -> List[str]:
    """
    Get list of sections available for tagging.

    Returns:
        List of display names for taggable sections
    """
    return [
        "Overview",
        "Requirements (Functional)",
        "Requirements (Technical)",
        "User Stories",
        "Acceptance Criteria",
        "Technical Specification",
        "Success Metrics",
    ]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def format_duration(seconds: float) -> str:
    """Format duration in MM:SS format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def estimate_word_count(text: str) -> int:
    """Estimate word count from text."""
    return len(text.split()) if text else 0


def get_segment_summary(segments: List[TaggedSegment]) -> Dict[str, int]:
    """
    Get summary of word counts per section.

    Args:
        segments: List of tagged segments

    Returns:
        Dict mapping section to word count
    """
    summary = {}
    for seg in segments:
        word_count = estimate_word_count(seg.text)
        summary[seg.section] = summary.get(seg.section, 0) + word_count
    return summary
