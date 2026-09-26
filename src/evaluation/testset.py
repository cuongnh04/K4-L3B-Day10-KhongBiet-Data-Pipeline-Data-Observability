from __future__ import annotations

from typing import Any

import pandas as pd


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    import json
    test_set = []
    if df.empty:
        return test_set
        
    # Generate 10 questions across 4 categories
    papers = df.head(5).to_dict('records')
    
    for i, p in enumerate(papers):
        # 1. Summary question
        test_set.append({
            'id': f'q_sum_{i}',
            'question_type': 'summary',
            'question': f"What is the main topic of the paper '{p['title']}'?",
            'ground_truth': p['summary'],
            'ground_truth_doc_ids': [p['paper_id']]
        })
        # 2. Authors question
        test_set.append({
            'id': f'q_auth_{i}',
            'question_type': 'authors',
            'question': f"Who are the authors of the paper '{p['title']}'?",
            'ground_truth': p['authors_joined'],
            'ground_truth_doc_ids': [p['paper_id']]
        })
        
    # Just keep exactly 10 questions for benchmark
    test_set = test_set[:10]
    
    # We could add date and categories if we want to vary
    if len(papers) > 0:
        test_set[8] = {
            'id': 'q_date_0',
            'question_type': 'date',
            'question': f"When was the paper '{papers[0]['title']}' published?",
            'ground_truth': str(papers[0]['published']),
            'ground_truth_doc_ids': [papers[0]['paper_id']]
        }
        test_set[9] = {
            'id': 'q_cat_0',
            'question_type': 'categories',
            'question': f"What are the categories for '{papers[0]['title']}'?",
            'ground_truth': papers[0]['categories_joined'],
            'ground_truth_doc_ids': [papers[0]['paper_id']]
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(test_set, f, indent=2)
        
    return test_set
