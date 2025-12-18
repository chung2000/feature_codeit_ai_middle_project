from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from src.common.config import config

class RFPMetadata(BaseModel):
    """Key information extracted from an RFP document."""
    project_name: Optional[str] = Field(None, description="The official name of the project or tender.")
    organization: Optional[str] = Field(None, description="The name of the organization issuing the RFP (e.g., public agency, company).")
    budget: Optional[str] = Field(None, description="The budget amount or estimated price (e.g., '100,000,000 KRW'). Keep the unit.")
    period: Optional[str] = Field(None, description="The duration of the project (e.g., '5 months', 'until 2024-12-31').")
    deadline: Optional[str] = Field(None, description="The submission deadline for the proposal (YYYY-MM-DD HH:MM format if possible).")

class MetadataExtractor:
    def __init__(self):
        llm_name = config.get("model.llm_name", "gpt-5")
        # Ensure we use a model capable of structured output or strict JSON
        self.llm = ChatOpenAI(model=llm_name, temperature=0)
        
        # Define the extraction chain
        # relying on with_structured_output if available, or just standard prompting
        if hasattr(self.llm, "with_structured_output"):
             self.extract_chain = self.llm.with_structured_output(RFPMetadata)
        else:
             # Fallback if older langchain version or model doesn't support it directly
             # But gpt-5/gpt-4o usually supports tool calling which with_structured_output uses
             pass 

    def extract(self, text: str) -> RFPMetadata:
        """
        Extract metadata from the provided text (usually the first few pages).
        """
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are an expert at analyzing Request for Proposal (RFP) documents. Extract the following key information from the provided text. If a field is not found, set it to null."),
            ("human", "{text}")
        ])
        
        chain = prompt | self.extract_chain
        
        try:
            # Simple truncation to avoid context limit if text is huge (though we generally pass first few pages)
            input_text = text[:10000] 
            return chain.invoke({"text": input_text})
        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return RFPMetadata()
