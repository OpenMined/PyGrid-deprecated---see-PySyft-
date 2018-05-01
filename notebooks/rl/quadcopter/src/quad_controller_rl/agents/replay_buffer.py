import random

from collections import namedtuple


Experience = namedtuple("Experience",
    field_names=["state", "action", "reward", "next_state", "done"])


class ReplayBuffer:
    """Fixed-size circular buffer to store experience tuples."""

    def __init__(self, size=1024):
        """Initialize a ReplayBuffer object."""
        self.size = size  # maximum size of buffer
        self.memory = []
        self.idx = 0  # current index into circular buffer
    
    def add(self, state, action, reward, next_state, done):
        """Add a new experience to memory."""
        # Note: If memory is full, start overwriting from the beginning
        experience = Experience(state, action, reward, next_state, done)
        if len(self.memory) < self.size:
            self.memory.append(experience)
        else:
            self.memory[self.idx] = experience
            self.idx += 1
            self.idx %= self.size
    
    def sample(self, batch_size=64):
        """Randomly sample a batch of experiences from memory."""
        return random.sample(self.memory, batch_size)

    def __len__(self):
        """Return the current size of internal memory."""
        return len(self.memory)
