import os
from dotenv import load_dotenv

_ = load_dotenv()

from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct, Document

print("Initializing Qdrant client...")
client = QdrantClient(
    url=os.getenv("QDRANT_URI"),
    api_key=os.getenv("QDRANT_API_KEY"),
    cloud_inference=True,
    check_compatibility=False,
)

TEST_PAPERS = [
    {
        "title": "Attention Is All You Need",
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. In an encoder-decoder configuration. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.",
    },
    {
        "title": "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
        "abstract": "We introduce BERT, a new method of pre-training language representations. Unlike recent language representation models, BERT is designed to pre-train deep bidirectional representations from unlabeled text by jointly conditioning on both left and right context in all layers. As a result, the pre-trained BERT model can be fine-tuned with just one additional output layer to create state-of-the-art models for a wide range of tasks, such as question answering and language inference, without substantial task-specific architecture modifications.",
    },
    {
        "title": "LSTM: A Search Space Odyssey",
        "abstract": "Several variants of the long short-term memory (LSTM) architecture have been proposed, each with different numbers of gates and activations. The question of what works best for LSTMs has not yet been answered. We conduct the first systematic study to compare different LSTM variants and provide practical recommendations for practitioners.",
    },
    {
        "title": "Graph Convolutional Networks for Semi-Supervised Node Classification",
        "abstract": "We present a scalable approach for semi-supervised learning on graphs based on an efficient variant of convolutional neural networks that operate directly on graphs. The method is based on a localized first-order approximation of spectral graph convolutions. Our framework combines neural networks with the non-Euclidean structure of graphs, enabling end-to-end learning of hidden layer representations for tasks on graphs.",
    },
    {
        "title": "Deep Residual Learning for Image Recognition",
        "abstract": "Very deep convolutional networks have led to groundbreaking advances in image recognition. However, as networks become increasingly deep, they become harder to train due to the vanishing gradient problem. To address this, we introduce a residual learning framework to ease training of networks that are substantially deeper than previously practical. We explicitly reformulate the layers as learning residual functions with reference to the layer inputs, instead of learning unreferenced functions.",
    },
]

points = [
    PointStruct(
        id=i,
        payload={
            "title": paper["title"],
            "abstract": paper["abstract"],
            "topic": "technology",
            "type": "research_paper",
            "paper_id": f"paper_{i}",
            "paper_url": f"https://arxiv.org/abs/{i:04d}",
            "keywords": "",
        },
        vector={
            "intfloat/multilingual-e5-small": Document(
                text=f"{paper['title']} {paper['abstract']}",
                model="intfloat/multilingual-e5-small",
            )
        },
    )
    for i, paper in enumerate(TEST_PAPERS)
]

if client.collection_exists("test-col"):
    print("Collection exists. Deleting and recreating...")
    client.delete_collection("test-col")

print("Creating collection...")
client.create_collection(
    collection_name="test-col",
    vectors_config={
        "intfloat/multilingual-e5-small": models.VectorParams(
            size=384,
            distance=models.Distance.COSINE,
        )
    },
    quantization_config=models.ScalarQuantization(
        scalar=models.ScalarQuantizationConfig(
            type=models.ScalarType.INT8,
            always_ram=True,
        ),
    ),
)

print("Upserting points...")
client.upsert(collection_name="test-col", points=points)

print("Querying points...")
points = client.query_points(
    collection_name="test-col",
    query=Document(
        text="transformer models for natural language processing",
        model="intfloat/multilingual-e5-small",
    ),
    using="intfloat/multilingual-e5-small",
)

print(points)
