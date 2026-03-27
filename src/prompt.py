SUMMARY_PROMPT_TEMPLATE = """
        Task: Analyze the financial news context and the extracted relationship nodes to generate a comprehensive analysis. The response must strictly adhere to the specified Thai Markdown structure and focus on high-level strategy.

        Response Language: Primary Thai. All explanations and descriptive text must be in Thai. **However, all proper nouns and company names (e.g., Microsoft, Google, Nvidia, OpenAI) must be written in English.**
        Response Format: Strictly use the two required headers in Markdown (##) followed by synthesized content.

        Context:
        ---
        News Article:
        {article_context}
        ---

        Instructions for Output Generation:

        1.  **Header 1 - ภาพรวมเชิงลึก (Insight Overview):**
            * Start the entire analysis with this header: `## ภาพรวมเชิงลึก (Insight Overview)`
            * Content should be a synthesis of the news and relationships, identifying major market **trends**, **implications**, and the overall competitive landscape or regulatory environment. (Must be a cohesive paragraph or multiple paragraphs, not bullet points).
            * response briefly in 3-4 lines.

        2.  **Header 2 - ทิศทางเชิงกลยุทธ์ของบริษัท:**
            * Follow the first section immediately with this header: `## ทิศทางเชิงกลยุทธ์ของบริษัท`
            * Identify the **key companies** involved.
            * For each company, use **bullet points** (`*`) to clearly describe their **strategic moves, competitive position, investments, or challenges** as indicated by the context.
            * response briefly in 1-2 lines.

        3.  **Do not include any other introductory text, final remarks, or headers besides the two specified ones.**

        Analysis (Summary):
        """

RISK_PROMPT_TEMPLATE = """
        Task: Analyze the financial news context and the extracted relationship nodes to identify and evaluate potential **Key Risks** associated with the situation.

        Response Language: Primary Thai. All explanations and descriptive text must be in Thai. **However, all proper nouns and company names (e.g., Microsoft, Google, Nvidia, OpenAI) must be written in English.**
        Response Format: Strict Markdown to list and detail the identified risks, followed by an explanation and citation (if available).

        Context:
        ---
        News Article:
        {article_context}
        ---

        Instructions for Risk Analysis:

        1.  **Identify Key Risks:** Based on the news context in English, identify at least three major potential risks (e.g., Regulatory Scrutiny, Supply Chain Issues, Intensified Competition, Geopolitical Tension, Economic Downturn, Technology Failure).
        2.  **Provide Detail:**
            * State the risk in bold (e.g., **Regulatory Scrutiny**).
            * Provide a brief **Thai explanation** of *why* this risk is relevant to the context.
            * If the context explicitly mentions a source or impact related to the risk, include it in the explanation.
        3.  **Output Structure:**
            * Start the entire output with the heading: `## ⚠️ ความเสี่ยงที่ควรระวัง`
            * Format each risk as a collapsible section or clearly separate entries using Markdown structure, prioritizing clarity and scannability similar to the example image.

        Analysis (Summary):
        """

DIRECTION_PROMPT_TEMPLATE = """
        Task: Analyze the financial news context to summarize the strategic position and key actions of the main companies/entities involved. The output must be structured as individual summaries for each entity.

        Response Language: Primary Thai. All explanations and descriptive text must be in Thai. **However, all proper nouns and company names (e.g., Microsoft, Google, Nvidia, OpenAI) must be written in English.**
        Response Format: Use Markdown to list each entity's strategic summary clearly.

        Context:
        ---
        News Article:
        {article_context}
        ---

        Instructions for Strategic Output:

        1.  **Identify Key Entities:** Identify 3-4 major players (e.g., Microsoft, OpenAI, Nvidia, Google, AMD) from the context.
        2.  **Entity Block:** For each entity, create a block with the following structure:
            * **Header:** Start with the name in bold and use an appropriate icon (e.g., **Microsoft**).
            * **Summary:** Provide a concise, high-level summarizing their strategic focus (e.g., "Aggressively expanding AI capabilities through strategic investments and partnerships.").
            * **Key Actions:** Provide a bulleted list of 3-5 specific actions or capabilities derived from the news (e.g., Expanding Azure AI services, Integrating AI into Windows, Developing custom silicon).

        Analysis (Strategic Summary):
        """

TEXT2GRAPH_PROMPT_TEMPLATE = """
    Task: Generate a Neo4j Cypher query to answer the user's question.
    Schema:
    {schema}
    
    Instructions:
    - Use only the provided schema.
    - Return ONLY the Cypher query, no markdown, no explanation.
    - The query should return nodes and relationships if possible, or specific data if asked.
    - Use COALESCE(n.name, n.id) for names.
    - If the user asks about "investments", look for INVESTS_IN relationships.
    - If the user asks about "partnerships", look for PARTNERS_WITH relationships.
    Question: {question} กราฟ
    Cypher Query:
    """
