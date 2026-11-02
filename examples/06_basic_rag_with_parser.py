from langchain_core.output_parsers import StrOutputParser

from app.chains import get_llm, format_docs
from app.prompts import rag_prompt
from app.rag import load_documents, split_documents
from app.vectorstore import build_vectorstore, get_retriever


docs = load_documents()
chunks = split_documents(docs)

db = build_vectorstore(chunks)
retriever = get_retriever(db)

llm = get_llm()
parser = StrOutputParser()


def retrieve_context(inputs):
    question = inputs["question"]
    retrieved_docs = retriever.invoke(question)

    # rag_prompt expects {context} and {rewritten_question}. This simple example does
    # no question rewriting, so the rewritten question is just the original question.
    return {
        "question": question,
        "rewritten_question": question,
        "context": format_docs(retrieved_docs),
    }


chain = retrieve_context | rag_prompt | llm | parser

result = chain.invoke({
    "question": "How many vacation days do full-time store employees receive?"
})

print(result)