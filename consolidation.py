import re

def get_node_text(node: dict) -> str:
    """Safely extract all text components of a node to avoid KeyError."""
    parts = []
    for key in ['label', 'headline', 'title', 'rationale', 'description', 'subheadline']:
        val = node.get(key)
        if val:
            parts.append(str(val))
    return " ".join(parts)

def tokenize(text: str) -> set:
    """Normalize and tokenize text into a set of unique words for Jaccard calculation."""
    words = re.sub(r'[^\w\s]', '', text.lower()).split()
    # Remove basic stop words to isolate semantic meaning on CPU
    stop_words = {'i', 'am', 'the', 'a', 'an', 'to', 'for', 'of', 'in', 'is', 'on', 'about', 'my', 'and', 'but', 'or', 'with', 'by', 'at'}
    return set(w for w in words if w not in stop_words)

def compute_jaccard(set_a: set, set_b: set) -> float:
    if not set_a or not set_b:
        return 0.0
    return len(set_a.intersection(set_b)) / len(set_a.union(set_b))

def consolidate_nodes(nodes: list, similarity_threshold: float) -> list:
    consolidated = []
    
    for incoming in nodes:
        incoming_text = get_node_text(incoming)
        incoming_tokens = tokenize(incoming_text)
        merged = False
        
        for existing in consolidated:
            existing_text = get_node_text(existing)
            existing_tokens = tokenize(existing_text)
            similarity = compute_jaccard(incoming_tokens, existing_tokens)
            
            if similarity >= similarity_threshold:
                # Merge logic: Retain the highest quality description, merge provenance lists
                existing_prov = existing.get('provenance', [])
                incoming_prov = incoming.get('provenance', [incoming.get('origin_worker', 'unknown')])
                for prov_item in incoming_prov:
                    if prov_item not in existing_prov:
                        existing_prov.append(prov_item)
                existing['provenance'] = existing_prov
                existing['consensus_score'] = existing.get('consensus_score', 1.0) + 0.2  # Reward consensus ideas
                merged = True
                break
                
        if not merged:
            if 'provenance' not in incoming:
                incoming['provenance'] = [incoming.get('origin_worker', 'unknown')]
            incoming['consensus_score'] = 1.0
            consolidated.append(incoming)
            
    return consolidated
