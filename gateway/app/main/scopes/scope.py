import uuid


class Scope:
    def __init__(self, user_id: str, protocol):
        self.creator = user_id
        self.id = str(uuid.uuid4())
        self.assignments = {self.creator: "assignment-1"}
        self.plan_number = {self.creator: 0}
        self.protocol = protocol

    def add_participant(self, participant_id: str):
        self.workers.add(participant_id)

        # Check if already exist an assignment / plan number defined to this id.
        assignment = self.assignments.get(participant_id, None)
        plan_number = self.plan_number.get(participant_id, None)

        if not assignment:
            self.assignment[participant_id] = "assignment-" + len(self.assignments) + 1
        if not plan_number:
            self.plan_number[participant_id] = len(self.plan_number) + 1

    def get_role(self, participant_id: str) -> str:
        if participant_id in self.assignments:
            if participant_id == self.creator:
                return "creator"
            else:
                return "participant"

    def plan_number(self, participant_id: str) -> int:
        return self.plan_number[participant_id]

    def assignment_position(self, participant_id: str) -> str:
        return self.assignments[participant_id]

    def get_participants(self) -> list:
        return filter(lambda x: self.plan_number[x] != 0, self.plan_number.keys())
