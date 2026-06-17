# Helix Platform Quick Start Guide

Get up and running with Helix Platform in 5 minutes.

---

## Installation (2 minutes)

### Prerequisites
- Python 3.9+
- pip or conda
- API keys for at least one LLM provider (OpenRouter, Anthropic, Groq, OpenAI)

### Step 1: Clone and Setup

```bash
git clone https://github.com/Deathcharge/helix-platform.git
cd helix-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure API Keys

Create a `.env` file:

```bash
# .env
OPENROUTER_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
```

Or set environment variables:

```bash
export OPENROUTER_API_KEY=your_key_here
export ANTHROPIC_API_KEY=your_key_here
```

---

## Your First Agent Swarm (3 minutes)

Create `my_first_swarm.py`:

```python
"""
Your first Helix Platform multi-agent system.
This example creates 3 agents that work together to analyze a topic.
"""

from helix_agent_swarm import HelixOrchestrator
from unified_llm import LLMClient
from ucf_protocol import UCFProtocol

# Step 1: Create orchestrator
print("🚀 Creating agent orchestrator...")
orchestrator = HelixOrchestrator()

# Step 2: Register agents
print("👥 Registering agents...")

orchestrator.register_agent(
    name="researcher",
    agent_type="Gemini",
    system_prompt="""You are a research specialist.
Your job is to gather comprehensive information on topics.
Be thorough and cite sources when possible."""
)

orchestrator.register_agent(
    name="validator",
    agent_type="Kavach",
    system_prompt="""You are a fact validator.
Your job is to check claims and assess credibility.
Be skeptical and look for potential biases."""
)

orchestrator.register_agent(
    name="synthesizer",
    agent_type="Agni",
    system_prompt="""You are a knowledge synthesizer.
Your job is to create coherent summaries from multiple sources.
Connect ideas and highlight key insights."""
)

# Step 3: Create LLM client
print("🧠 Initializing LLM client...")
llm = LLMClient(provider="openrouter")

# Step 4: Execute task
print("\n📋 Task: Analyze the impact of AI on society")
print("-" * 50)

# Get research from first agent
print("\n1️⃣  Researcher gathering information...")
research = llm.generate({
    "prompt": "What are the key impacts of AI on society?",
    "system": orchestrator.agents["researcher"].system_prompt,
    "max_tokens": 500
})
print(f"Research findings:\n{research}\n")

# Get validation from second agent
print("2️⃣  Validator checking facts...")
validation = llm.generate({
    "prompt": f"Validate these claims: {research}",
    "system": orchestrator.agents["validator"].system_prompt,
    "max_tokens": 300
})
print(f"Validation results:\n{validation}\n")

# Get synthesis from third agent
print("3️⃣  Synthesizer creating summary...")
synthesis = llm.generate({
    "prompt": f"Create a summary: {research}",
    "system": orchestrator.agents["synthesizer"].system_prompt,
    "max_tokens": 400
})
print(f"Final synthesis:\n{synthesis}\n")

# Step 5: Monitor system health
print("-" * 50)
print("📊 System Metrics")
state = orchestrator.get_state()
metrics = UCFProtocol().calculate_metrics(state)

print(f"✅ System Harmony: {metrics.harmony:.2f}/1.0")
print(f"✅ System Resilience: {metrics.resilience:.2f}/1.0")
print(f"✅ Current Phase: {metrics.phase}")

print("\n✨ Multi-agent analysis complete!")
```

### Run It

```bash
python my_first_swarm.py
```

### Expected Output

```
🚀 Creating agent orchestrator...
👥 Registering agents...
🧠 Initializing LLM client...

📋 Task: Analyze the impact of AI on society
--------------------------------------------------

1️⃣  Researcher gathering information...
Research findings:
AI is transforming society through...

2️⃣  Validator checking facts...
Validation results:
These claims are generally accurate...

3️⃣  Synthesizer creating summary...
Final synthesis:
AI's impact on society includes...

--------------------------------------------------
📊 System Metrics
✅ System Harmony: 0.87/1.0
✅ System Resilience: 0.92/1.0
✅ Current Phase: HARMONIOUS

✨ Multi-agent analysis complete!
```

---

## Next Examples to Try

### Example 2: Consensus Voting

Agents vote on proposals and make collective decisions:

```bash
python examples/02_consensus_voting.py
```

### Example 3: Scheduled Workflows

Execute complex workflows on a schedule:

```bash
python examples/03_scheduled_workflow.py
```

### Example 4: Customer Support System

Build a complete support system with specialized agents:

```bash
python examples/04_customer_support.py
```

---

## Common Patterns

### Pattern 1: Sequential Agent Processing

Process information through multiple agents in sequence:

```python
# Agent 1 processes
result1 = llm.generate({"prompt": "...", "system": agent1_prompt})

# Agent 2 processes result from Agent 1
result2 = llm.generate({"prompt": result1, "system": agent2_prompt})

# Agent 3 processes result from Agent 2
result3 = llm.generate({"prompt": result2, "system": agent3_prompt})
```

### Pattern 2: Parallel Agent Processing

Process with multiple agents in parallel:

```python
from concurrent.futures import ThreadPoolExecutor

def process_with_agent(agent_name, prompt):
    return llm.generate({
        "prompt": prompt,
        "system": orchestrator.agents[agent_name].system_prompt
    })

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(
        lambda agent: process_with_agent(agent, prompt),
        orchestrator.agents.keys()
    ))
```

### Pattern 3: Consensus Voting

Have agents vote on a proposal:

```python
from agent_consensus import ConsensusEngine, Proposal

consensus = ConsensusEngine()

proposal = Proposal(
    title="Deploy new feature",
    description="Should we deploy the new feature?",
    details={"timeline": "1 week", "risk": "low"}
)

result = consensus.vote(
    proposal=proposal,
    agents=list(orchestrator.agents.values()),
    strategy="supermajority"
)

if result.agreed:
    print("✅ Proposal approved!")
else:
    print("❌ Proposal rejected")
```

---

## Configuration

### Basic Configuration

```python
from helix_agent_swarm import HelixOrchestrator

# Create with custom settings
orchestrator = HelixOrchestrator(
    max_agents=50,
    communication_timeout=30,
    agent_timeout=300,
    enable_metrics=True,
    enable_persistence=True
)
```

### LLM Configuration

```python
from unified_llm import LLMClient

# Use different providers
llm = LLMClient(provider="anthropic")  # Anthropic Claude
llm = LLMClient(provider="groq")       # Groq (free)
llm = LLMClient(provider="openrouter") # OpenRouter (multiple models)
llm = LLMClient(provider="openai")     # OpenAI GPT
llm = LLMClient(provider="ollama")     # Local Ollama
```

### Agent Customization

```python
# Create custom agent with specific personality
orchestrator.register_agent(
    name="creative",
    agent_type="Agni",
    system_prompt="""You are a creative thinker...
    
Your personality:
- Think outside the box
- Suggest innovative solutions
- Challenge conventional wisdom

Your constraints:
- Stay practical and implementable
- Consider resource constraints
- Align with team goals""",
    
    # Optional: custom parameters
    temperature=0.8,  # More creative
    max_tokens=2000,
    personality_profile={
        "creativity": 0.9,
        "caution": 0.3,
        "collaboration": 0.8
    }
)
```

---

## Monitoring & Debugging

### Check System Health

```python
# Get current state
state = orchestrator.get_state()

# Get metrics
metrics = UCFProtocol().calculate_metrics(state)

print(f"Agents active: {len(state.agents)}")
print(f"Messages processed: {state.message_count}")
print(f"Harmony: {metrics.harmony:.2f}")
print(f"Phase: {metrics.phase}")
```

### Enable Logging

```python
import logging

# Set log level
logging.basicConfig(level=logging.DEBUG)

# Now you'll see detailed logs
orchestrator = HelixOrchestrator()
```

### View Agent State

```python
# Get specific agent state
agent = orchestrator.agents["researcher"]
print(f"Agent: {agent.name}")
print(f"Type: {agent.agent_type}")
print(f"Status: {agent.status}")
print(f"Tasks completed: {agent.task_count}")
print(f"Last activity: {agent.last_activity}")
```

---

## Troubleshooting

### Issue: "API Key not found"

**Solution**: Make sure your API key is set:

```bash
# Check environment variable
echo $OPENROUTER_API_KEY

# Or set it
export OPENROUTER_API_KEY=your_key_here
```

### Issue: "Agent timeout"

**Solution**: Increase timeout or check LLM provider:

```python
orchestrator = HelixOrchestrator(agent_timeout=600)  # 10 minutes
```

### Issue: "Low harmony score"

**Solution**: Check agent alignment and communication:

```python
# Reduce number of agents
# Improve system prompts
# Increase communication timeout
orchestrator = HelixOrchestrator(communication_timeout=60)
```

### Issue: "Memory usage high"

**Solution**: Enable persistence and clear history:

```python
# Clear old messages
orchestrator.clear_message_history(older_than_hours=24)

# Enable persistence to disk
orchestrator.enable_persistence()
```

---

## Next Steps

1. **Explore Examples**: Check `examples/` for 4 complete examples
2. **Read Documentation**: See `docs/` for detailed guides
3. **Try Integration**: Build your own multi-agent system
4. **Deploy**: Use Docker or Kubernetes deployment guides
5. **Join Community**: Connect with other developers

---

## Resources

- **Full Documentation**: [docs/](docs/)
- **API Reference**: [docs/API_REFERENCE.md](docs/API_REFERENCE.md)
- **Architecture Guide**: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Integration Examples**: [examples/](examples/)
- **GitHub Issues**: Report bugs and request features
- **Community**: Join our Discord server

---

## Getting Help

- **Documentation**: https://docs.helix-platform.ai
- **GitHub Issues**: https://github.com/Deathcharge/helix-platform/issues
- **Email**: support@helix-platform.ai
- **Discord**: https://discord.gg/helix-platform

---

**Happy building! 🚀**
