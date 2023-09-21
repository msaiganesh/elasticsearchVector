from flask import Flask, request, jsonify
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import pandas as pd

app = Flask(__name__)

# Connect to Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

# Define your Elasticsearch index name
index_name = 'vector_search_index'

# Load a pre-trained Sentence Transformers model
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Create the Elasticsearch index with the static mapping
def create_index():
    mapping = {
        "mappings": {
            "properties": {
                "text_embedding": {
                    "type": "dense_vector",
                    "dims": 768  # Adjust to match your vector dimensionality
                },
                "text": {
                    "type": "text",
                    "index": True,
                    "analyzer": "standard"
                }
            }
        }
    }
    es.indices.create(index=index_name, body=mapping, ignore=400)

# Index the data from the TSV file along with vector embeddings
def index_data():
    tsv_file_path = 'your_data.tsv'  # Replace with the path to your TSV file
    df = pd.read_csv(tsv_file_path, sep='\t')
    
    for _, row in df.iterrows():
        text = row['text_column_name']  # Replace with the name of the text column in your TSV file
        text_embedding = model.encode(text).tolist()
        
        document = {
            "text_embedding": text_embedding,
            "text": text,
            "id": row['id_column_name']  # Replace with the name of the ID column in your TSV file
        }
        
        es.index(index=index_name, body=document)

# Perform a similarity search
def similarity_search(query_text):
    query_embedding = model.encode(query_text).tolist()
    similarity_query = {
        "query": {
            "script_score": {
                "query": {"match_all": {}},
                "script": {
                    "source": "cosineSimilarity(params.query_embedding, 'text_embedding') + 1.0",
                    "params": {"query_embedding": query_embedding}
                }
            }
        },
        "_source": ["text", "id"],
        "size": 5
    }

    results = es.search(index=index_name, body=similarity_query)

    # Extract and format the results
    formatted_results = []
    for hit in results['hits']['hits']:
        formatted_results.append({
            "id": hit['_source']['id'],
            "text": hit['_source']['text']
        })
    
    return formatted_results

@app.route('/create_index', methods=['POST'])
def create_index_route():
    create_index()
    return jsonify({"message": "Index created successfully"}), 200

@app.route('/index_data', methods=['POST'])
def index_data_route():
    index_data()
    return jsonify({"message": "Data indexed successfully"}), 200

@app.route('/search', methods=['POST'])
def search_route():
    if 'query' not in request.json:
        return jsonify({"error": "Missing 'query' parameter"}), 400

    query_text = request.json['query']
    results = similarity_search(query_text)
    return jsonify({"results": results}), 200

if __name__ == "__main__":
    app.run(debug=True)
