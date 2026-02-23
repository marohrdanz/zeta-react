This is a toy project for me to learn about ReAct (Reasoning and Acting) and how to use it in my projects.

```mermaid
%%{init: {'theme': 'neutral'}}%%
graph TD;
	__start__([<p>__start__</p>]):::first
	agent(agent)
	tools(tools)
	__end__([<p>__end__</p>]):::last
	__start__ --> agent;
	agent -.-> __end__;
	agent -.-> tools;
	tools --> agent;
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```

## Requirements

### Anthropic API Key

This project uses the Anthropic API. Add an API key to the .env file:

```text
ANTHROPIC_API_KEY=...
```

### Langfuse Instance

This project uses an external Langfuse instance to keep track of traces. Ask your
favorate AI about how to set one up (easy with docker), and add the following
envs to the .env file:

```text
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...
LANGFUSE_HOST=http://localhost:3000
```

## Example

Example question and response is shown below. By looking at the debugging output,
I can see the `get_major_scale`, `get_blues_scale`, and `search` tools used.

```text
╭──────────────────────────────────────────────────────────────────── User Question ─────────────────────────────────────────────────────────────────────╮
│ Question: What notes are shared between the C blues scale and the F major scale? Would those shared notes work well for immprovising over ii-V-I in C? │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
╭──────────────────────────────────────────────────────────────────────────────────────── Agent Response ────────────────────────────────────────────────────────────────────────────────────────╮
│ Response: Cool. So the shared notes between the C blues scale and F major scale are:                                                                                                           │
│ - **C**                                                                                                                                                                                        │
│ - **F**                                                                                                                                                                                        │
│ - **G**                                                                                                                                                                                        │
│ - **A#** (Bb)                                                                                                                                                                                  │
│                                                                                                                                                                                                │
│ Now, let's talk about ii-V-I in C major. That's Dm7 - G7 - Cmaj7, right?                                                                                                                       │
│                                                                                                                                                                                                │
│ Those shared notes would give you C, F, G, and Bb. Let me break this down for you:                                                                                                             │
│                                                                                                                                                                                                │
│ - Over **Dm7** (D-F-A-C): You got the C, F, and Bb. That Bb is the 6th of D minor - sweet tension there.                                                                                       │
│ - Over **G7** (G-B-D-F): You got G and F (the 7th) plus C (the 4th). Missing that B natural though, which is the major 3rd that defines the dominant quality.                                  │
│ - Over **Cmaj7** (C-E-G-B): You got C and G, the root and fifth - solid, but you're missing that E and B that give it that major 7 color.                                                      │
│                                                                                                                                                                                                │
│ Here's the thing, man - those notes alone? Too limited. You'd be playing it safe, real middle-of-the-road. When I'm blowing over changes, I need the whole palette. That Bb over G7 is hip,    │
│ creates that blue note tension, but you need that B natural too to outline the dominant. And where's your chromaticism? Where's your edge?                                                     │
│                                                                                                                                                                                                │
│ The blues scale is about feeling and grit, but ii-V-I is about harmonic movement and resolution. You gotta mix both vocabularies - use the blues inflections but respect the changes. Play the │
│ B natural over that G7, then bend into your blue notes. That's where the magic happens.                                                                                                        │
│                                                                                                                                                                                                │
│ Don't limit yourself to just those intersection notes. Use the *whole* thing.                                                                                                                  │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```
