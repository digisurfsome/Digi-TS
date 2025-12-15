// State
const state = {
  tool: 'select', // select, move, arrow, rect, text
  color: '#ef4444',
  lineWidth: 4,
  chunks: [],
  annotations: [],
  history: [],
  isDrawing: false,
  startX: 0,
  startY: 0,
  currentX: 0,
  currentY: 0,
  draggedChunk: null,
  dragOffsetX: 0,
  dragOffsetY: 0,
  baseImage: null,
  canvasOffsetX: 0,
  canvasOffsetY: 0
};

// DOM Elements
const canvas = document.getElementById('mainCanvas');
const ctx = canvas.getContext('2d');
const canvasContainer = document.getElementById('canvasContainer');
const chunksLayer = document.getElementById('chunksLayer');
const selectionBox = document.getElementById('selectionBox');
const statusText = document.getElementById('statusText');
const chunkCount = document.getElementById('chunkCount');

// Initialize
async function init() {
  // Load screenshot from storage
  const data = await chrome.storage.local.get(['screenshot']);
  if (data.screenshot) {
    loadImage(data.screenshot);
  } else {
    statusText.textContent = 'No screenshot found - capture a page first';
  }

  setupEventListeners();

  // Show instructions on first use
  const hasSeenInstructions = localStorage.getItem('mockup-instructions-seen');
  if (!hasSeenInstructions) {
    document.getElementById('instructionsModal').classList.remove('hidden');
  } else {
    document.getElementById('instructionsModal').classList.add('hidden');
  }
}

function loadImage(dataUrl) {
  const img = new Image();
  img.onload = () => {
    state.baseImage = img;
    canvas.width = img.width;
    canvas.height = img.height;
    render();
    updateCanvasOffset();
    statusText.textContent = 'Ready - Draw a rectangle to select a chunk';
  };
  img.src = dataUrl;
}

function updateCanvasOffset() {
  const rect = canvas.getBoundingClientRect();
  state.canvasOffsetX = rect.left;
  state.canvasOffsetY = rect.top;
}

// Event Listeners
function setupEventListeners() {
  // Tool buttons
  document.getElementById('selectTool').addEventListener('click', () => setTool('select'));
  document.getElementById('moveTool').addEventListener('click', () => setTool('move'));
  document.getElementById('arrowTool').addEventListener('click', () => setTool('arrow'));
  document.getElementById('rectTool').addEventListener('click', () => setTool('rect'));
  document.getElementById('textTool').addEventListener('click', () => setTool('text'));

  // Color buttons
  document.querySelectorAll('.color-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.color-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.color = btn.dataset.color;
    });
  });

  // Line width
  document.getElementById('lineWidth').addEventListener('change', (e) => {
    state.lineWidth = parseInt(e.target.value);
  });

  // Action buttons
  document.getElementById('undoBtn').addEventListener('click', undo);
  document.getElementById('clearChunks').addEventListener('click', clearAll);
  document.getElementById('exportBtn').addEventListener('click', exportImage);

  // Modal
  document.getElementById('closeModal').addEventListener('click', () => {
    document.getElementById('instructionsModal').classList.add('hidden');
    localStorage.setItem('mockup-instructions-seen', 'true');
  });

  // Text input
  document.getElementById('textSubmit').addEventListener('click', submitText);
  document.getElementById('textInput').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') submitText();
  });

  // Canvas events
  canvas.addEventListener('mousedown', handleMouseDown);
  canvas.addEventListener('mousemove', handleMouseMove);
  canvas.addEventListener('mouseup', handleMouseUp);
  canvas.addEventListener('mouseleave', handleMouseUp);

  // Window resize
  window.addEventListener('resize', updateCanvasOffset);
  window.addEventListener('scroll', updateCanvasOffset);

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;

    switch(e.key.toLowerCase()) {
      case 'v': setTool('select'); break;
      case 'm': setTool('move'); break;
      case 'a': setTool('arrow'); break;
      case 'r': setTool('rect'); break;
      case 't': setTool('text'); break;
      case 'z': if (e.ctrlKey || e.metaKey) undo(); break;
      case 'escape': cancelAction(); break;
    }
  });
}

function setTool(tool) {
  state.tool = tool;
  document.querySelectorAll('.tool-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById(tool + 'Tool')?.classList.add('active');

  // Update cursor
  canvas.style.cursor = tool === 'move' ? 'grab' : 'crosshair';

  // Update status
  const statusMessages = {
    select: 'Draw a rectangle to select a chunk',
    move: 'Click and drag chunks to move them',
    arrow: 'Click and drag to draw an arrow',
    rect: 'Click and drag to draw a rectangle',
    text: 'Click to place text'
  };
  statusText.textContent = statusMessages[tool] || 'Ready';

  // Hide text input if switching away
  if (tool !== 'text') {
    document.getElementById('textInputContainer').classList.add('hidden');
  }
}

function getMousePos(e) {
  updateCanvasOffset();
  const rect = canvas.getBoundingClientRect();
  const scaleX = canvas.width / rect.width;
  const scaleY = canvas.height / rect.height;
  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY
  };
}

function handleMouseDown(e) {
  const pos = getMousePos(e);
  state.isDrawing = true;
  state.startX = pos.x;
  state.startY = pos.y;

  if (state.tool === 'text') {
    showTextInput(e.clientX, e.clientY, pos.x, pos.y);
    state.isDrawing = false;
  }
}

function handleMouseMove(e) {
  if (!state.isDrawing) return;

  const pos = getMousePos(e);
  state.currentX = pos.x;
  state.currentY = pos.y;

  if (state.tool === 'select') {
    // Show selection box
    const rect = canvas.getBoundingClientRect();
    const scaleX = rect.width / canvas.width;
    const scaleY = rect.height / canvas.height;

    const left = Math.min(state.startX, state.currentX) * scaleX + rect.left;
    const top = Math.min(state.startY, state.currentY) * scaleY + rect.top;
    const width = Math.abs(state.currentX - state.startX) * scaleX;
    const height = Math.abs(state.currentY - state.startY) * scaleY;

    selectionBox.style.display = 'block';
    selectionBox.style.left = left + 'px';
    selectionBox.style.top = top + 'px';
    selectionBox.style.width = width + 'px';
    selectionBox.style.height = height + 'px';
  } else if (state.tool === 'arrow' || state.tool === 'rect') {
    // Live preview
    render();
    drawAnnotationPreview();
  }
}

function handleMouseUp(e) {
  if (!state.isDrawing) return;
  state.isDrawing = false;

  const pos = getMousePos(e);
  state.currentX = pos.x;
  state.currentY = pos.y;

  selectionBox.style.display = 'none';

  if (state.tool === 'select') {
    createChunk();
  } else if (state.tool === 'arrow' || state.tool === 'rect') {
    createAnnotation();
  }
}

function createChunk() {
  const x = Math.min(state.startX, state.currentX);
  const y = Math.min(state.startY, state.currentY);
  const width = Math.abs(state.currentX - state.startX);
  const height = Math.abs(state.currentY - state.startY);

  if (width < 10 || height < 10) return; // Too small

  // Create image data for the chunk
  const chunkCanvas = document.createElement('canvas');
  chunkCanvas.width = width;
  chunkCanvas.height = height;
  const chunkCtx = chunkCanvas.getContext('2d');
  chunkCtx.drawImage(state.baseImage, x, y, width, height, 0, 0, width, height);

  const chunk = {
    id: 'chunk-' + Date.now(),
    originalX: x,
    originalY: y,
    x: x,
    y: y,
    width: width,
    height: height,
    imageData: chunkCanvas.toDataURL()
  };

  state.chunks.push(chunk);
  saveHistory();
  createChunkElement(chunk);
  updateChunkCount();
  render();
}

function createChunkElement(chunk) {
  const rect = canvas.getBoundingClientRect();
  const scaleX = rect.width / canvas.width;
  const scaleY = rect.height / canvas.height;

  const div = document.createElement('div');
  div.className = 'chunk';
  div.id = chunk.id;
  div.style.left = (chunk.x * scaleX + rect.left) + 'px';
  div.style.top = (chunk.y * scaleY + rect.top) + 'px';
  div.style.width = (chunk.width * scaleX) + 'px';
  div.style.height = (chunk.height * scaleY) + 'px';

  const img = document.createElement('img');
  img.src = chunk.imageData;
  img.style.width = '100%';
  img.style.height = '100%';
  img.draggable = false;
  div.appendChild(img);

  // Delete button
  const deleteBtn = document.createElement('button');
  deleteBtn.className = 'chunk-delete';
  deleteBtn.innerHTML = '×';
  deleteBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    deleteChunk(chunk.id);
  });
  div.appendChild(deleteBtn);

  // Drag events
  div.addEventListener('mousedown', (e) => startDragChunk(e, chunk));

  chunksLayer.appendChild(div);
}

function startDragChunk(e, chunk) {
  if (state.tool !== 'select' && state.tool !== 'move') return;

  e.preventDefault();
  const div = document.getElementById(chunk.id);
  div.classList.add('dragging');

  const rect = canvas.getBoundingClientRect();
  const scaleX = rect.width / canvas.width;
  const scaleY = rect.height / canvas.height;

  state.draggedChunk = chunk;
  state.dragOffsetX = e.clientX - (chunk.x * scaleX + rect.left);
  state.dragOffsetY = e.clientY - (chunk.y * scaleY + rect.top);

  const moveHandler = (e) => dragChunk(e);
  const upHandler = () => {
    document.removeEventListener('mousemove', moveHandler);
    document.removeEventListener('mouseup', upHandler);
    endDragChunk();
  };

  document.addEventListener('mousemove', moveHandler);
  document.addEventListener('mouseup', upHandler);
}

function dragChunk(e) {
  if (!state.draggedChunk) return;

  const rect = canvas.getBoundingClientRect();
  const scaleX = rect.width / canvas.width;
  const scaleY = rect.height / canvas.height;

  const newX = (e.clientX - state.dragOffsetX - rect.left) / scaleX;
  const newY = (e.clientY - state.dragOffsetY - rect.top) / scaleY;

  state.draggedChunk.x = newX;
  state.draggedChunk.y = newY;

  const div = document.getElementById(state.draggedChunk.id);
  div.style.left = (newX * scaleX + rect.left) + 'px';
  div.style.top = (newY * scaleY + rect.top) + 'px';

  render();
}

function endDragChunk() {
  if (state.draggedChunk) {
    const div = document.getElementById(state.draggedChunk.id);
    div.classList.remove('dragging');
    saveHistory();
  }
  state.draggedChunk = null;
}

function deleteChunk(id) {
  state.chunks = state.chunks.filter(c => c.id !== id);
  const div = document.getElementById(id);
  if (div) div.remove();
  saveHistory();
  updateChunkCount();
  render();
}

function createAnnotation() {
  const annotation = {
    type: state.tool,
    startX: state.startX,
    startY: state.startY,
    endX: state.currentX,
    endY: state.currentY,
    color: state.color,
    lineWidth: state.lineWidth
  };

  if (Math.abs(annotation.endX - annotation.startX) < 5 &&
      Math.abs(annotation.endY - annotation.startY) < 5) return;

  state.annotations.push(annotation);
  saveHistory();
  render();
}

function drawAnnotationPreview() {
  if (state.tool === 'arrow') {
    drawArrow(ctx, state.startX, state.startY, state.currentX, state.currentY, state.color, state.lineWidth);
  } else if (state.tool === 'rect') {
    drawRect(ctx, state.startX, state.startY, state.currentX, state.currentY, state.color, state.lineWidth);
  }
}

function drawArrow(ctx, fromX, fromY, toX, toY, color, lineWidth) {
  const headLength = 15 + lineWidth * 2;
  const angle = Math.atan2(toY - fromY, toX - fromX);

  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.lineCap = 'round';

  // Line
  ctx.beginPath();
  ctx.moveTo(fromX, fromY);
  ctx.lineTo(toX, toY);
  ctx.stroke();

  // Arrowhead
  ctx.beginPath();
  ctx.moveTo(toX, toY);
  ctx.lineTo(toX - headLength * Math.cos(angle - Math.PI / 6), toY - headLength * Math.sin(angle - Math.PI / 6));
  ctx.lineTo(toX - headLength * Math.cos(angle + Math.PI / 6), toY - headLength * Math.sin(angle + Math.PI / 6));
  ctx.closePath();
  ctx.fill();
}

function drawRect(ctx, x1, y1, x2, y2, color, lineWidth) {
  ctx.strokeStyle = color;
  ctx.lineWidth = lineWidth;
  ctx.strokeRect(
    Math.min(x1, x2),
    Math.min(y1, y2),
    Math.abs(x2 - x1),
    Math.abs(y2 - y1)
  );
}

function showTextInput(clientX, clientY, canvasX, canvasY) {
  const container = document.getElementById('textInputContainer');
  container.classList.remove('hidden');
  container.style.left = clientX + 'px';
  container.style.top = clientY + 'px';
  container.dataset.canvasX = canvasX;
  container.dataset.canvasY = canvasY;
  document.getElementById('textInput').focus();
}

function submitText() {
  const container = document.getElementById('textInputContainer');
  const input = document.getElementById('textInput');
  const text = input.value.trim();

  if (text) {
    const annotation = {
      type: 'text',
      x: parseFloat(container.dataset.canvasX),
      y: parseFloat(container.dataset.canvasY),
      text: text,
      color: state.color,
      fontSize: 16 + state.lineWidth * 4
    };
    state.annotations.push(annotation);
    saveHistory();
    render();
  }

  input.value = '';
  container.classList.add('hidden');
}

function render() {
  if (!state.baseImage) return;

  // Clear canvas
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw base image
  ctx.drawImage(state.baseImage, 0, 0);

  // Draw "holes" where chunks were cut (darkened areas)
  ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
  state.chunks.forEach(chunk => {
    ctx.fillRect(chunk.originalX, chunk.originalY, chunk.width, chunk.height);
  });

  // Draw annotations
  state.annotations.forEach(ann => {
    if (ann.type === 'arrow') {
      drawArrow(ctx, ann.startX, ann.startY, ann.endX, ann.endY, ann.color, ann.lineWidth);
    } else if (ann.type === 'rect') {
      drawRect(ctx, ann.startX, ann.startY, ann.endX, ann.endY, ann.color, ann.lineWidth);
    } else if (ann.type === 'text') {
      ctx.font = `bold ${ann.fontSize}px -apple-system, sans-serif`;
      ctx.fillStyle = ann.color;
      ctx.fillText(ann.text, ann.x, ann.y);
    }
  });
}

function saveHistory() {
  state.history.push({
    chunks: JSON.parse(JSON.stringify(state.chunks)),
    annotations: JSON.parse(JSON.stringify(state.annotations))
  });
  // Keep only last 20 states
  if (state.history.length > 20) state.history.shift();
}

function undo() {
  if (state.history.length < 2) return;

  state.history.pop(); // Remove current state
  const prevState = state.history[state.history.length - 1];

  if (prevState) {
    state.chunks = prevState.chunks;
    state.annotations = prevState.annotations;
    rebuildChunks();
    render();
    updateChunkCount();
  }
}

function rebuildChunks() {
  chunksLayer.innerHTML = '';
  state.chunks.forEach(chunk => createChunkElement(chunk));
}

function clearAll() {
  if (!confirm('Clear all chunks and annotations?')) return;

  state.chunks = [];
  state.annotations = [];
  chunksLayer.innerHTML = '';
  saveHistory();
  render();
  updateChunkCount();
}

function updateChunkCount() {
  chunkCount.textContent = `Chunks: ${state.chunks.length}`;
}

function cancelAction() {
  state.isDrawing = false;
  selectionBox.style.display = 'none';
  document.getElementById('textInputContainer').classList.add('hidden');
  render();
}

async function exportImage() {
  statusText.textContent = 'Exporting...';

  // Create export canvas
  const exportCanvas = document.createElement('canvas');
  exportCanvas.width = canvas.width;
  exportCanvas.height = canvas.height;
  const exportCtx = exportCanvas.getContext('2d');

  // Draw base with holes
  exportCtx.drawImage(canvas, 0, 0);

  // Draw chunks at their new positions
  for (const chunk of state.chunks) {
    const img = new Image();
    await new Promise(resolve => {
      img.onload = resolve;
      img.src = chunk.imageData;
    });
    exportCtx.drawImage(img, chunk.x, chunk.y);
  }

  // Create download
  const dataUrl = exportCanvas.toDataURL('image/png');
  const filename = `mockup-${Date.now()}.png`;

  // Use chrome downloads API
  chrome.runtime.sendMessage({
    action: 'download',
    dataUrl: dataUrl,
    filename: filename
  });

  statusText.textContent = 'Exported! Check your downloads.';
}

// Handle window resize to reposition chunks
window.addEventListener('resize', () => {
  updateCanvasOffset();
  rebuildChunks();
});

// Start
init();
