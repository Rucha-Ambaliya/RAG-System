import os
import requests
import time
from difflib import SequenceMatcher

API_URL = "http://127.0.0.1:8000"  # change if your API runs elsewhere
SAMPLE_DIR = "tests/sample_documents"

# Example queries and expected answers for evaluation
TEST_QUERIES = {
    "book.txt": [
        {
            "query": "Who does Alice follow?",
            "expected": "Alice follows a White Rabbit with pink eyes."
        },
        {
            "query": "What event starts Alice's adventure?",
            "expected": "Alice sees the White Rabbit take a watch from its waistcoat and follows it down a rabbit-hole."
        }
    ],
    "paper.pdf": [
        {
            "query": "What is the main argument of the document?",
            "expected": "AI transforms education by improving accessibility, personalization, and scalability."
        },
        {
            "query": "Explain AI impact in education",
            "expected": "AI improves learning efficiency, engagement, and reduces teachers' administrative workload."
        }
    ],
    "report.docx": [
        {
            "query": "What is the main argument of the document?",
            "expected": "AI acts as a catalyst for improving learning efficiency, engagement, and accessibility."
        },
        {
            "query": "Explain AI impact in education",
            "expected": "AI supports adaptive learning, personalization, accessibility, and helps teachers with tasks."
        }
    ]
}

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# ------------------- Embed documents -------------------
embedded_docs = []
for file_name in os.listdir(SAMPLE_DIR):
    file_path = os.path.join(SAMPLE_DIR, file_name)
    if not os.path.isfile(file_path):
        continue

    with open(file_path, 'rb') as f:
        files = {'file': (file_name, f)}
        start = time.time()
        resp = requests.post(f"{API_URL}/api/embedding", files=files)
        end = time.time()
        data = resp.json()

        if data.get('status') == 'success':
            print(f"Embedded {file_name} in {end-start:.2f}s. Document ID: {data['document_id']}")
            embedded_docs.append({"file_name": file_name, "document_id": data['document_id']})
        else:
            print(f"Failed to embed {file_name}: {data}")

# ------------------- Query documents -------------------
THRESHOLD = 0.6  # similarity threshold for correctness

for doc in embedded_docs:
    print(f"\n=== Metrics for {doc['file_name']} ===")
    total_response_time = 0
    queries = TEST_QUERIES.get(doc['file_name'], [])
    for q in queries:
        start = time.time()
        resp = requests.post(f"{API_URL}/api/query", data={
            'query': q['query'],
            'document_id': doc['document_id'],
            'require_citations': True
        })
        end = time.time()
        total_response_time += (end - start)
        data = resp.json()

        answer = data.get('response', {}).get('answer', '')
        citations = data.get('response', {}).get('citations', [])
        score = similarity(answer, q['expected'])
        correctness = 'Correct' if score >= THRESHOLD else 'Incorrect'

        print("------------------------------")
        print(f"Query: {q['query']}")
        print(f"Answer: {answer}")
        print(f"Citations: {citations}")
        print(f"Response Time: {end-start:.2f}s")
        print(f"Similarity Score: {score:.2f}")
        print(f"Correctness: {correctness}")

    avg_time = total_response_time / max(len(queries), 1)
    print(f"\nAverage Response Time for {doc['file_name']}: {avg_time:.2f}s")
