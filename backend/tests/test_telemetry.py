import sys
import os
import asyncio
import json
import types

# Ensure backend package modules import correctly
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
backend_path = os.path.join(repo_root, 'backend')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

import core.planner as planner_mod
import core.model_router as model_router_mod
import agents.swarm_manager as swarm_mod
import api.websocket as websocket_mod


class MockManager:
    def __init__(self, raise_on_broadcast=False):
        self.messages = []
        self.raise_on_broadcast = raise_on_broadcast

    async def broadcast(self, message):
        if self.raise_on_broadcast:
            raise Exception("broadcast failure")
        # store a shallow copy to avoid mutation races
        self.messages.append(json.loads(json.dumps(message)))

    def get_connection_count(self):
        # Pretend there is at least one connection for loops that check this
        return 1

    def get_connection_info(self):
        return {}


def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_planner_emits_planner_state(monkeypatch):
    # Replace websocket manager with mock
    mock = MockManager()
    monkeypatch.setattr(websocket_mod, 'manager', mock)

    async def inner():
        p = planner_mod.Planner()
        plan = await p.create_plan("What is your current status?", [], {})
        # allow scheduled broadcast task to run
        await asyncio.sleep(0.05)
        # find planner_state message
        found = [m for m in mock.messages if m.get('type') == 'planner_state']
        assert found, "planner_state was not broadcast"
        data = found[0].get('data', {})
        assert 'plan_id' in data
        assert 'intent' in data
        assert 'confidence' in data
        assert 'task_type' in data
        assert 'steps' in data

    asyncio.run(inner())


def test_model_router_emits_model_state(monkeypatch):
    mock = MockManager()
    monkeypatch.setattr(websocket_mod, 'manager', mock)

    async def inner():
        router = model_router_mod.ModelRouter()

        # Monkeypatch availability check to control behavior
        async def always_available(name):
            return True

        monkeypatch.setattr(router, 'is_model_available', always_available)

        sel = await router.select_model(planner_mod.TaskType.GENERAL_QUESTION, 'simple')
        # allow scheduled broadcast task to run
        await asyncio.sleep(0.05)
        found = [m for m in mock.messages if m.get('type') == 'model_state']
        assert found, "model_state was not broadcast"
        data = found[0].get('data', {})
        assert 'model' in data
        assert 'category' in data
        assert 'reason' in data
        assert 'routing_meta' in data
        assert 'fallback_used' in data

    asyncio.run(inner())


def test_swarm_manager_agent_state_emissions(monkeypatch):
    mock = MockManager()
    monkeypatch.setattr(websocket_mod, 'manager', mock)

    async def inner():
        swarm = swarm_mod.SwarmManager(None)
        swarm.is_initialized = True

        # Create a fake agent that matches by name
        class FakeAgent:
            def __init__(self):
                self.agent_name = 'coding_agent'

            async def get_status(self):
                return {'specializations': ['coding']}

            async def process_request(self, request, context=None):
                return {'response': 'ok', 'metadata': {}}

        fake = FakeAgent()
        # register by key that select_agent_for_step will inspect
        swarm.agent_instances['coding_agent'] = fake
        swarm.agents[swarm_mod.AgentType.CODING] = fake

        # Create a TaskStep that mentions coding
        step = planner_mod.TaskStep(id='s1', description='Please write some coding logic')

        agent, key, reason = await swarm.select_agent_for_step(step)
        assert agent is not None
        await asyncio.sleep(0.05)

        # ensure an agent_state 'selected' message was broadcast
        found_selected = [m for m in mock.messages if m.get('type') == 'agent_state' and m.get('data', {}).get('status') == 'selected']
        assert found_selected, "agent_state selected not broadcast"

        # Now test executing a SwarmTask start/completion broadcasts
        from datetime import datetime
        task = swarm_mod.SwarmTask(task_id='task1', description='Run task', required_agents=[swarm_mod.AgentType.CODING], priority=swarm_mod.TaskPriority.MEDIUM)
        # Run the execution directly
        await swarm._execute_task(task)
        await asyncio.sleep(0.05)
        # look for started/completed messages
        started = [m for m in mock.messages if m.get('type') == 'agent_state' and m.get('data', {}).get('status') == 'started']
        completed = [m for m in mock.messages if m.get('type') == 'agent_state' and m.get('data', {}).get('status') in ('completed','failed')]
        assert started, "agent_state started not broadcast"
        assert completed, "agent_state completion not broadcast"

    asyncio.run(inner())


def test_system_snapshot_loop_broadcasts_and_is_resilient(monkeypatch):
    mock = MockManager()
    monkeypatch.setattr(websocket_mod, 'manager', mock)

    class FakeSI:
        async def get_live_snapshot(self):
            return {'cpu': 'low', 'health': 'ok'}

        async def get_memory_status(self):
            return {'short_term': 10, 'long_term': 5, 'health': 'ok'}

        async def get_system_status(self):
            return {'cpu': 10, 'memory': 40}

    class FakeBrain:
        def __init__(self):
            self.system_intelligence = FakeSI()

    async def inner():
        brain = FakeBrain()
        # Run the loop in background and cancel after a short period
        task = asyncio.create_task(websocket_mod.system_snapshot_broadcast_loop(brain, interval=0.05))
        await asyncio.sleep(0.15)
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        types_seen = {m.get('type') for m in mock.messages}
        assert 'system_snapshot' in types_seen
        assert 'memory_state' in types_seen
        assert 'system_state' in types_seen

    asyncio.run(inner())


def test_broadcast_failures_do_not_raise(monkeypatch):
    mock = MockManager(raise_on_broadcast=True)
    monkeypatch.setattr(websocket_mod, 'manager', mock)

    async def inner():
        # Planner should not raise even if broadcast fails
        p = planner_mod.Planner()
        plan = await p.create_plan("Will this fail?", [], {})

        # ModelRouter should not raise either
        router = model_router_mod.ModelRouter()

        async def always_available(name):
            return True

        monkeypatch.setattr(router, 'is_model_available', always_available)
        sel = await router.select_model(planner_mod.TaskType.GENERAL_QUESTION, 'simple')

        # SwarmManager selection should also be safe
        swarm = swarm_mod.SwarmManager(None)
        swarm.is_initialized = True
        step = planner_mod.TaskStep(id='s2', description='generic step')
        # no agents registered -> should return (None, None, 'no_agent_available') without raising
        agent, key, reason = await swarm.select_agent_for_step(step)

        assert plan is not None
        assert sel is not None

    asyncio.run(inner())
