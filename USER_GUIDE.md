# Design Tree Studio - User Guide

A simple guide to help you use Design Tree Studio effectively.

---

## Quick Start (2 minutes)

1. **Select a User** - Use the dropdown in the left sidebar
2. **Select or Create a Project** - Click the project dropdown or "+ New" button
3. **Start Chatting** - Type in the chat box on the left to talk to AI
4. **Organize Ideas** - Use the Design Tree tab to create and manage components

---

## The Interface

### Left Side: AI Chat
This is where you talk to the AI about your project.

- **Type your message** in the text box
- **Send** to get AI responses
- **Clear** to start fresh
- **Baton Now** - Creates a snapshot and starts a new session (use when running low on tokens)

The **Token Usage** bar shows how much of your context budget you've used. When it gets high (orange/red), consider creating a baton.

### Right Side: Tabs

| Tab | What It Does |
|-----|--------------|
| **System Status** | Shows if everything is configured correctly |
| **Settings** | Configure API keys, models, and preferences |
| **Project Context** | Add background info the AI should know about |
| **Design Tree** | Create and manage your project components |
| **Truth Doc** | Export your entire project as documentation |
| **Process Log** | See what's happening behind the scenes (debugging) |

---

## Core Features Explained

### 1. Projects
A **Project** is a container for all your work. Each project has:
- Its own chat sessions
- Its own nodes/components
- Its own context
- Separate from other projects

**To create a project:**
1. Click "+ New" in the sidebar
2. Enter a name
3. Click Create

### 2. Design Tree (Nodes)
The Design Tree is where you organize your project into **Nodes**. Think of nodes as building blocks or components of your project.

**Node Types:**
- 🌳 **Root** - Top level item
- 📁 **Folder** - Group related things together
- 🧩 **Component** - A specific part/feature
- 🎨 **Asset** - Design elements, images, etc.
- 📝 **Note** - Random thoughts or documentation

**Node Statuses:**
- 🟡 **Draft** - Work in progress
- 🟢 **Active** - Finalized/ready
- 🔵 **Archived** - No longer active
- 🔴 **Deleted** - Marked for removal

**To create a node:**
1. Go to Design Tree tab
2. Fill in Name, Type, Description
3. Click "Create Node"

### 3. Rant → Summary
Don't know how to organize your thoughts? Just dump them!

1. Go to **Design Tree** → **Rant → Summary** tab
2. Type your raw thoughts (messy is fine!)
3. Click **✨ Summarize**
4. AI organizes it into structured content
5. Save it as a new node or attach to existing one

### 4. Project Context
This is background info that the AI always knows about when chatting.

1. Go to **Project Context** tab
2. Add context like:
   - Project goals
   - Design guidelines
   - Technical requirements
   - Brand voice
3. This info is automatically included in every AI conversation

### 5. Baton System
When you chat, you use "tokens" (like words). There's a limit. The **Baton** system solves this:

**What happens:**
1. You chat until tokens get high
2. Click "Baton Now" (or it auto-triggers)
3. AI creates a summary of everything so far
4. A fresh chat session starts with that summary as context
5. You continue where you left off!

**Auto Baton:** When your token usage hits the threshold (default 80%), it automatically suggests creating a baton.

### 6. Truth Doc Export
Export your entire project as a single markdown document.

1. Go to **Truth Doc** tab
2. Click **Generate Truth Doc**
3. Preview it
4. Click **Download** to save as .md file

Great for:
- Documentation
- Handoffs to others
- Backing up your work
- Sharing project status

---

## Settings Reference

| Setting | What It Does |
|---------|--------------|
| **OpenAI API Key** | Your API key (leave blank if using environment variable) |
| **Default Chat Model** | Which AI model to use (e.g., gpt-4-turbo-preview) |
| **Default Summary Model** | Model for summaries and auto-descriptions |
| **Max Context Tokens** | How many tokens before suggesting a baton |
| **Auto Baton Threshold** | Percentage at which to auto-suggest baton (e.g., 80) |
| **Warmup Prompts 1-4** | Messages sent to AI when starting a warmed session |

---

## Common Workflows

### Starting a New Design Project
1. Create a new Project
2. Add Project Context with your requirements/goals
3. Chat with AI to brainstorm
4. Create Nodes for each component you identify
5. Keep iterating!

### Organizing Messy Ideas
1. Go to Rant → Summary
2. Brain dump everything
3. Let AI organize it
4. Create nodes from the summary
5. Refine each node individually

### Long Design Sessions
1. Chat normally
2. Watch token usage bar
3. When it gets high, click "Baton Now"
4. Continue in the new session
5. The AI remembers context from the baton

### Exporting Your Work
1. Go to Truth Doc tab
2. Generate and preview
3. Download the markdown file
4. Share with teammates or save for later

---

## Tips & Tricks

1. **Be specific in chat** - The AI works better with detailed questions
2. **Use Project Context** - The more context you provide, the better AI responses
3. **Create Nodes early** - Helps organize as you go
4. **Draft status is your friend** - Use it for work-in-progress items
5. **Check Process Log** - If something seems wrong, look here for clues
6. **Baton before it's too late** - Don't wait until you hit 100% tokens

---

## Troubleshooting

### "OpenAI API key not configured"
Go to Settings tab and enter your API key, OR set it in Railway environment variables.

### Chat not responding
1. Check Process Log for errors
2. Verify API key is correct
3. Check your OpenAI account has credits

### Design Tree shows error
Refresh the page. If it persists, check System Status tab for database issues.

### Lost my work
- Chat history is saved per session
- Nodes are saved immediately when created
- Truth Doc can export everything

---

## Need Help?

- **System Status tab** - Shows what's working/broken
- **Process Log tab** - Shows detailed activity
- Check the error messages - they usually say what's wrong

---

*Design Tree Studio v0.1.0*
