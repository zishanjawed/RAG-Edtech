import asyncio
import sys
import os
import re
from datetime import datetime
from typing import Dict, List, Tuple
import httpx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class RAGEvaluator:
    def __init__(self, base_url: str, token: str, content_id: str):
        self.base_url = base_url
        self.token = token
        self.content_id = content_id
        self.results = []
    
    async def evaluate_question(
        self,
        question: str,
        expected_keywords: List[str],
        category: str
    ) -> Dict:
        start_time = datetime.utcnow()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/api/query/{self.content_id}/complete",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"question": question, "user_id": "evaluator"}
            )
        
        elapsed_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        if response.status_code != 200:
            return {
                "question": question,
                "category": category,
                "error": response.text,
                "response_time_ms": elapsed_ms
            }
        
        data = response.json()
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        metadata = data.get("metadata", {})
        
        answer_lower = answer.lower()
        exact_matches = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
        
        fuzzy_matches = 0
        for kw in expected_keywords:
            if kw.lower() not in answer_lower:
                pattern = r'\b\w*' + re.escape(kw[:min(4, len(kw))]) + r'\w*\b'
                if re.search(pattern, answer_lower, re.IGNORECASE):
                    fuzzy_matches += 1
        
        keyword_matches = exact_matches + fuzzy_matches
        keyword_score = keyword_matches / len(expected_keywords) if expected_keywords else 0
        
        return {
            "question": question,
            "category": category,
            "answer": answer,
            "answer_length": len(answer),
            "response_time_ms": elapsed_ms,
            "sources_count": len(sources),
            "keyword_coverage": keyword_score,
            "keywords_found": keyword_matches,
            "keywords_expected": len(expected_keywords),
            "tokens_used": metadata.get("tokens_used", {}).get("total_tokens", 0),
            "chunks_used": metadata.get("chunks_used", 0),
            "has_citations": "[Source" in answer,
            "similarity_scores": [s.get("similarity_score", 0) for s in sources],
        }
    
    def generate_report(self) -> str:
        if not self.results:
            return "No results to report"
        
        successful_results = [r for r in self.results if "error" not in r]
        
        if not successful_results:
            return "All evaluations failed"
        
        avg_response = sum(r["response_time_ms"] for r in successful_results) / len(successful_results)
        avg_keywords = sum(r["keyword_coverage"] for r in successful_results) / len(successful_results)
        citation_rate = sum(1 for r in successful_results if r["has_citations"]) / len(successful_results)
        avg_tokens = sum(r["tokens_used"] for r in successful_results) / len(successful_results)
        avg_chunks = sum(r["chunks_used"] for r in successful_results) / len(successful_results)
        
        all_similarity_scores = [score for r in successful_results for score in r.get("similarity_scores", [])]
        avg_similarity = sum(all_similarity_scores) / len(all_similarity_scores) if all_similarity_scores else 0
        
        report = f"""
{'='*80}
RAG PIPELINE EVALUATION REPORT
{'='*80}
Generated: {datetime.utcnow().isoformat()}
Content ID: {self.content_id}
Total Questions: {len(self.results)}
Successful: {len(successful_results)}
Failed: {len(self.results) - len(successful_results)}

PERFORMANCE METRICS
{'-'*80}
Average Response Time:    {avg_response:>10.2f} ms
Average Keyword Coverage: {avg_keywords:>10.1%}
Citation Rate:            {citation_rate:>10.1%}
Average Tokens Used:      {avg_tokens:>10.0f}
Average Chunks Used:      {avg_chunks:>10.1f}
Average Similarity Score: {avg_similarity:>10.3f}

DETAILED RESULTS BY CATEGORY
{'-'*80}
"""
        
        categories = {}
        for result in successful_results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
        
        for category, results in categories.items():
            cat_avg_response = sum(r["response_time_ms"] for r in results) / len(results)
            cat_avg_keywords = sum(r["keyword_coverage"] for r in results) / len(results)
            cat_citation_rate = sum(1 for r in results if r["has_citations"]) / len(results)
            
            report += f"""
{category.upper()}
  Questions: {len(results)}
  Avg Response Time: {cat_avg_response:.2f} ms
  Keyword Coverage: {cat_avg_keywords:.1%}
  Citation Rate: {cat_citation_rate:.1%}
"""
        
        report += f"""
{'='*80}
QUESTION-BY-QUESTION BREAKDOWN
{'='*80}
"""
        
        for i, result in enumerate(self.results, 1):
            if "error" in result:
                report += f"""
Q{i}. {result['question'][:60]}...
   ERROR: {result['error']}
"""
            else:
                status = "PASS" if result["keyword_coverage"] >= 0.6 and result["has_citations"] else "REVIEW"
                report += f"""
Q{i}. {result['question'][:60]}...
   Category: {result['category']}
   Status: {status}
   Response Time: {result['response_time_ms']:.0f} ms
   Keyword Coverage: {result['keywords_found']}/{result['keywords_expected']} ({result['keyword_coverage']:.1%})
   Sources: {result['sources_count']} | Chunks: {result['chunks_used']} | Tokens: {result['tokens_used']}
   Has Citations: {"Yes" if result['has_citations'] else "No"}
   Answer Length: {result['answer_length']} chars
"""
        
        report += f"""
{'='*80}
EVALUATION SUMMARY
{'='*80}
Pass Criteria:
  - Response Time < 30000 ms:     {"PASS" if avg_response < 30000 else "FAIL"}
  - Keyword Coverage >= 60%:      {"PASS" if avg_keywords >= 0.6 else "FAIL"}
  - Citation Rate >= 90%:         {"PASS" if citation_rate >= 0.9 else "FAIL"}
  - Avg Similarity Score >= 0.7:  {"PASS" if avg_similarity >= 0.7 else "FAIL"}

Overall Status: {"PASS" if (avg_response < 30000 and avg_keywords >= 0.6 and citation_rate >= 0.9 and avg_similarity >= 0.7) else "NEEDS IMPROVEMENT"}
{'='*80}
"""
        
        return report


async def main():
    BASE_URL = "http://localhost:8000"
    
    login_response = await httpx.AsyncClient().post(
        f"{BASE_URL}/api/auth/login",
        json={"email": "tony.stark@edtech.com", "password": "TestPass@123"}
    )
    token = login_response.json()["access_token"]
    
    CONTENT_ID_ML = "495e721e-ede7-462d-9c08-f49f2c638cd4"
    
    evaluator = RAGEvaluator(BASE_URL, token, CONTENT_ID_ML)
    
    test_questions = [
        ("What is the formula for F1 Score?", 
         ["f1", "precision", "recall", "formula"], 
         "factual_recall"),
        
        ("List three optimization techniques mentioned in the document",
         ["gradient", "descent", "adam", "momentum", "rmsprop", "adagrad", "optimizer"],
         "factual_recall"),
        
        ("What are the LSTM gates?",
         ["forget", "input", "output", "gates"],
         "factual_recall"),
        
        ("Compare K-Means clustering with decision trees",
         ["clustering", "decision tree", "unsupervised", "supervised"],
         "comparison"),
        
        ("What is the difference between L1 and L2 regularization?",
         ["l1", "l2", "lasso", "ridge", "regularization"],
         "comparison"),
        
        ("How does ReLU differ from Sigmoid activation?",
         ["relu", "sigmoid", "activation", "function"],
         "comparison"),
        
        ("Which deep learning architecture would be best for time series prediction?",
         ["rnn", "lstm", "sequential", "time series"],
         "application"),
        
        ("Name three companies using autonomous vehicle technology",
         ["tesla", "waymo"],
         "application"),
        
        ("Explain the vanishing gradient problem",
         ["vanishing", "gradient", "rnn", "backpropagation"],
         "conceptual"),
    ]
    
    print("Starting RAG Pipeline Evaluation...")
    print(f"Testing {len(test_questions)} questions against content {CONTENT_ID_ML}")
    print("-" * 80)
    
    for i, (question, keywords, category) in enumerate(test_questions, 1):
        print(f"\nEvaluating Q{i}/{len(test_questions)}: {question[:60]}...")
        result = await evaluator.evaluate_question(question, keywords, category)
        evaluator.results.append(result)
        
        if "error" not in result:
            print(f"  Time: {result['response_time_ms']:.0f}ms | Keywords: {result['keyword_coverage']:.1%} | Sources: {result['sources_count']}")
        else:
            print(f"  ERROR: {result['error'][:50]}")
    
    print("\n" + "="*80)
    print("Generating Report...")
    print("="*80)
    
    report = evaluator.generate_report()
    print(report)
    
    report_file = f"/Users/zishan/RAG-Edtech/docs/rag_evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\nReport saved to: {report_file}")


if __name__ == "__main__":
    asyncio.run(main())

