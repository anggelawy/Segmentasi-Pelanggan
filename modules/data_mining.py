from sklearn.cluster import KMeans
from sklearn.metrics import davies_bouldin_score
# Parent class untuk clustering
class DataMining:
    def __init__(self):
        self.clustering_results = None
        self.dbi_score = None

    def apply_clustering(self, transformed_data, num_clusters):
        clustering_data = transformed_data[['Recency_normalized', 'Frequency_normalized', 'Monetary_normalized']].dropna()

        kmeans = KMeans(n_clusters=num_clusters, random_state=42)
        kmeans.fit(clustering_data)

        transformed_data['Cluster'] = kmeans.labels_ + 1
        transformed_data['Cluster'] = transformed_data['Cluster'].astype(int)
        self.clustering_results = transformed_data
        self.dbi_score = round(davies_bouldin_score(clustering_data, kmeans.labels_), 3)

        return self.clustering_results, self.dbi_score
