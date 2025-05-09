# from .models import User, Product, UserInteraction
# from sklearn.metrics.pairwise import cosine_similarity
# from sklearn.feature_extraction.text import TfidfVectorizer
# import pandas as pd
# from scipy.sparse import csr_matrix
# from sklearn.decomposition import TruncatedSVD
# import numpy as np

# def recommend_products(user_id, top_n=5):
#     # Fetch user interactions
#     interactions = UserInteraction.objects.filter(user_id=user_id).select_related('product')
#     interacted_products = [interaction.product for interaction in interactions]

#     if not interacted_products:
#         return Product.objects.all()[:top_n]

#     # Get all products
#     all_products = Product.objects.all()
#     products_df = pd.DataFrame(
#         [{'id': p.id, 'description': p.description, 'category': p.category} for p in all_products]
#     )

#     # Create TF-IDF matrix for product descriptions
#     tfidf = TfidfVectorizer(stop_words='english')
#     tfidf_matrix = tfidf.fit_transform(products_df['description'])

#     # Find similarity scores
#     user_vector = tfidf_matrix[[p.id for p in interacted_products]]
#     similarity_scores = cosine_similarity(user_vector, tfidf_matrix)

#     # Rank products by similarity
#     similar_indices = similarity_scores.mean(axis=0).argsort()[::-1]
#     recommended_ids = products_df.iloc[similar_indices]['id'].tolist()[:top_n]

#     return Product.objects.filter(id__in=recommended_ids)






# def collaborative_filtering_recommendations(user_id, top_n=5):
#     # Fetch all user-product interactions
#     interactions = UserInteraction.objects.all()
#     data = pd.DataFrame(
#         [{'user_id': i.user.id, 'product_id': i.product.id, 'action': i.action} for i in interactions]
#     )

#     # Create a user-product matrix
#     data['value'] = data['action'].map({'view': 1, 'click': 2, 'purchase': 3})
#     user_product_matrix = data.pivot_table(index='user_id', columns='product_id', values='value', fill_value=0)

#     # Convert to sparse matrix
#     sparse_matrix = csr_matrix(user_product_matrix.values)

#     # Apply matrix factorization
#     model = TruncatedSVD(n_components=50, random_state=42)
#     latent_matrix = model.fit_transform(sparse_matrix)

#     # Get recommendations for the user
#     user_idx = user_product_matrix.index.tolist().index(user_id)
#     user_vector = latent_matrix[user_idx]
#     scores = user_vector @ latent_matrix.T

#     # Rank products by score
#     similar_users_idx = np.argsort(scores)[::-1][:top_n]
#     recommended_products = user_product_matrix.columns[similar_users_idx]

#     return Product.objects.filter(id__in=recommended_products)



# def hybrid_recommendations(user_id, top_n=5):
#     # Get content-based recommendations
#     content_recs = recommend_products(user_id, top_n * 2)
#     content_ids = [product.id for product in content_recs]

#     # Get collaborative filtering recommendations
#     collab_recs = collaborative_filtering_recommendations(user_id, top_n * 2)
#     collab_ids = [product.id for product in collab_recs]

#     # Merge recommendations and rank by weighted priority
#     combined_ids = list(set(content_ids + collab_ids))
#     weights = {pid: 0 for pid in combined_ids}

#     for pid in content_ids:
#         weights[pid] += 0.6  # Content-based weight
#     for pid in collab_ids:
#         weights[pid] += 0.4  # Collaborative filtering weight

#     # Sort by weights and return top N
#     sorted_ids = sorted(weights, key=weights.get, reverse=True)[:top_n]
#     return Product.objects.filter(id__in=sorted_ids)
