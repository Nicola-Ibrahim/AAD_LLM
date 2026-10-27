"""Generated source retained in memory instead of written to the study directory."""

from evolution.domain.interfaces.code_repository import CodeRepository


class MemoryCodeRepository(CodeRepository):
    def __init__(self) -> None:
        self.code: dict[tuple[int, int], str] = {}

    def save_code(self, code: str, iteration_num: int, experiment_id: int) -> str:
        self.code[experiment_id, iteration_num] = code
        return f"memory://experiment/{experiment_id}/iteration/{iteration_num}"

    def clear_experiment(self, experiment_id: int) -> None:
        self.code = {key: code for key, code in self.code.items() if key[0] != experiment_id}
