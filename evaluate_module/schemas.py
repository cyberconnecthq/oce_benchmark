from math import isclose
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from enum import Enum

class EvaluateTarget(Enum):
    ANSWER = "ANSWER"
    REASONING = "REASONING"
    TOOL_USE = "TOOL_USE"
    SOURCES = "SOURCES"

class ToolUse(BaseModel):
    call_id: str
    tool_name:str
    tool_description: str
    tool_input:str
    tool_output: Optional[str] = None

    def to_prompt(self, ignore_output:bool = False) -> str:
        prompt = f"Tool Name: {self.tool_name}\n"
        prompt += f"Tool Description: {self.tool_description}\n"
        prompt += f"Tool Input: {self.tool_input}\n"
        if not ignore_output:
            prompt += f"Tool Output: {self.tool_output}\n"
        return prompt


class ReasoningStep(BaseModel):
    step: int
    reasoning: Optional[str] = None
    # function_call: Optional[ToolUse] = None

    def to_prompt(self) -> str:
        prompt = f"Step {self.step}:\n"
        if self.reasoning:
            prompt += f"Reasoning: {self.reasoning}\n"
        # if self.function_call:
        #     prompt += f"Function Call: {self.function_call.to_prompt()}\n"
        return prompt

class Answer(BaseModel):
    answer: str
    reasoning_steps: List[ReasoningStep]
    function_calls: List[ToolUse]
    # sources: List[str]

    def to_prompt(self) -> str:
        prompt = f"Final Answer: {self.answer}\n"
        return prompt
    
    def to_question(self) -> str:
        prompt = f"Agent output: {self.answer}\nNow validate the answer TXs are correct, executable and result in the right balance change"
        return prompt



class EvaluateItem(BaseModel):
    step: Optional[int] = None
    target: EvaluateTarget
    points: float
    criteria: str

    def to_prompt(self) -> str:
        prompt = f"Step {self.step}:\n" if self.step else ""
        prompt += f"Worth Points: {self.points}\n"
        prompt += f"Criteria content: {self.criteria}\n"
        return prompt

class EvaluateData(BaseModel):
    items: List[EvaluateItem]
    
    @field_validator('items')
    @classmethod
    def validate_total_points(cls, items: List[EvaluateItem]) -> List[EvaluateItem]:
        total_points = sum(item.points for item in items)
        if abs(total_points - 10.0) != 0:
            raise ValueError(f"The total weight of all evaluation items must be exactly 10. Current total: {total_points}.")
        return items


class QuestionData(BaseModel):
    task_id: str
    question: str
    level: int
    category: str
    # tools:Optional[List[str]] = Field(description="The tools that can be used to answer the question")

    def to_prompt(self) -> str:
        prompt = f"Task ID: {self.task_id}\n"
        prompt += f"Question: {self.question}\n"
        return prompt
    
    def to_question(self) -> str:
        question = f"Give me the correct and executable TX json list(if need multi steps to achieve) that can be directly signed and sent for me to execute the task:'{self.question}'. Don't give the hex directly, use code to actually generate the hex."
        return question


class AnvilConfig(BaseModel):
    fork_url: str = Field(description="The fork url")
    fork_block_number: str = Field(description="The fork block number")
    balance: str = Field(description="The balance of the account")
    port: int = Field(description="The port of the anvil")

class BenchmarkItem(BaseModel):
    task_id: str
    question: str = Field(description="The question to be answered")
    level:Optional[int] = 1
    category:str
    # answer: Answer = Field(description="The agent system output")
    criteria: str = Field(description="The criteria to be evaluated")
    anvil_config: Optional[AnvilConfig] = Field(description="The anvil config", default=None)

    



class AnswerEvaluateResult(BaseModel):
    reason: Optional[str] = None
    score: float = Field(description="The score of the answer worth")

    def __str__(self) -> str:
        return f"Reason: {self.reason}\nScore: {self.score}"
    

class ReasoningEvaluateItem(BaseModel):
    step: int
    reason: Optional[str] = None
    score: float = Field(description="The score of the reasoning step worth")

    def __str__(self) -> str:
        return f"Step: {self.step}\nReason: {self.reason}\nScore: {self.score}"

class ReasoningEvaluateResult(BaseModel):
    items: List[ReasoningEvaluateItem]

    def __str__(self) -> str:
        return "\n".join([item.__str__() for item in self.items])


class ToolUseEvaluateItem(BaseModel):
    reason: Optional[str] = None
    score: float = Field(description="The score of the tool use worth")

    def __str__(self) -> str:
        return f"Reason: {self.reason}\nScore: {self.score}"

class ToolUseEvaluateResult(BaseModel):
    items: List[ToolUseEvaluateItem]

    def __str__(self) -> str:
        return "\n".join([item.__str__() for item in self.items])


class Usage(BaseModel):
    completion_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    time_cost: float = 0

class AgentOutputItem(BaseModel):
    task_id: Optional[str] = None
    question: Optional[str] = None
    answer: str
    usage:Optional[Usage] = None
    
    
    def to_question(self) -> str:
        prompt = f"Agent output: {self.answer}\nNow validate the answer TXs are correct, executable and result in the right balance change"
        return prompt

class EvaluateScore(BaseModel):

    answer_score: float = Field(description="The score of the agent get from the answer")

    evaluate_detail:Optional[str] = Field(description="The detail of the evaluation")
    model_name: str
    task_id:str
    level:int
    category:str



class EvaluateResult(BaseModel):
    """评估结果模型"""
    task_id: Optional[str] = None
    status: str = Field(description="评估状态: success 或 failed")
    
    # 成功时的字段
    score: Optional[EvaluateScore] = None
    result: Optional[str] = None
    metadata: Optional[dict] = None
    
    # 失败时的字段  
    error: Optional[str] = None
    
    @model_validator(mode='after')
    def validate_result_fields(self):
        """验证根据状态字段的合法性"""
        if self.status == "success":
            if self.score is None:
                raise ValueError("成功状态时score字段不能为空")
        elif self.status == "failed":
            if self.error is None:
                raise ValueError("失败状态时error字段不能为空")
        else:
            raise ValueError("status字段必须为'success'或'failed'")
        return self