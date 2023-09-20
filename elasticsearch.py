from flask import Flask, request, jsonify, render_template
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
import pandas as pd

app = Flask(__name__, static_folder='static')

# Connect to Elasticsearch
es = Elasticsearch([{'host': 'localhost', 'port': 9200}])

# Define your Elasticsearch index name
index_name = 'vector_search_index'

# Load a pre-trained Sentence Transformers model
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# Define a static mapping for the Elasticsearch index (same as previous code)
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

# Create the Elasticsearch index with the static mapping
if not es.indices.exists(index=index_name):
    es.indices.create(index=index_name, body=mapping, ignore=400)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query_text = request.form['query_text']

        # Encode the query text to get its vector representation
        query_embedding = model.encode(query_text).tolist()

        # Perform a similarity search
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
            "size": 5  # Return the top 5 similar documents
        }

        results = es.search(index=index_name, body=similarity_query)
        hits = results['hits']['hits']

        return render_template('index.html', query_text=query_text, results=hits)

    return render_template('index.html', query_text='', results=[])

if __name__ == '__main__':
    app.run(debug=True)
