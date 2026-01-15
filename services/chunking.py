import tiktoken

encoder = tiktoken.get_encoding("cl100k_base")

def chunk_text(text: str, max_tokens=400, overlap=50):
    tokens = encoder.encode(text)
    chunks = []

    start = 0
    while start < len(tokens):
        end = start + max_tokens
        chunk = encoder.decode(tokens[start:end])
        chunks.append(chunk)
        start = end - overlap

    return chunks
