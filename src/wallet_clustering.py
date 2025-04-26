import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from pathlib import Path
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import webbrowser
from threading import Timer

def load_wallet_data(json_file_path):
    print(f"Loading wallet data from {json_file_path}")
    with open(json_file_path, 'r') as f:
        wallet_data = json.load(f)
    
    df = pd.DataFrame.from_dict(wallet_data, orient='index')
    print(f"Loaded data for {len(df)} wallets with {len(df.columns)} features")
    print(f"Features: {', '.join(df.columns)}")
    
    if 'target' not in df.columns:
        print("No target feature found, setting default target to 'unknown'")
        df['target'] = "unknown"
    
    return df

def scale_features(df):
    print("Scaling features...")
    features_to_scale = df.drop('target', axis=1, errors='ignore')
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features_to_scale)
    
    return scaled_features, scaler

def cluster_wallets(scaled_data, n_clusters=5):
    print(f"Clustering wallets into {n_clusters} groups...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(scaled_data)
    return cluster_labels

def visualize_clusters(scaled_data, cluster_labels, wallet_addresses, output_path, df_original):
    print("Reducing dimensionality for visualization...")
    pca = PCA(n_components=2)
    reduced_data = pca.fit_transform(scaled_data)
    
    viz_df = pd.DataFrame(
        {
            'wallet_address': wallet_addresses,
            'cluster': cluster_labels.astype(str),
            'component_1': reduced_data[:, 0],
            'component_2': reduced_data[:, 1]
        }
    )
    
    if 'target' in df_original.columns:
        viz_df['target'] = df_original['target'].values
        color_column = 'target'
        color_title = 'Target'
    else:
        color_column = 'cluster'
        color_title = 'Cluster'
    
    explained_variance = pca.explained_variance_ratio_
    total_variance = sum(explained_variance) * 100
    
    plt.figure(figsize=(12, 8))
    
    unique_values = viz_df[color_column].unique()
    for value in unique_values:
        subset = viz_df[viz_df[color_column] == value]
        plt.scatter(subset['component_1'], subset['component_2'], 
                   label=f'{color_title} {value}', alpha=0.7)
    
    plt.title('Wallet Clusters Visualization')
    plt.xlabel(f'Principal Component 1 ({explained_variance[0]:.2%} variance)')
    plt.ylabel(f'Principal Component 2 ({explained_variance[1]:.2%} variance)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    plt.figtext(0.5, 0.01, f'Total variance explained: {total_variance:.2f}%', 
                ha='center', fontsize=12)
    
    plt.savefig(output_path)
    print(f"Static visualization saved to {output_path}")
    
    html_path = str(output_path).replace('.png', '_interactive.html')
    
    viz_df['hover_text'] = viz_df['wallet_address'].apply(lambda x: f"Wallet: {x[:10]}...")
    
    fig = px.scatter(
        viz_df,
        x='component_1',
        y='component_2',
        color=color_column,
        hover_data=['hover_text'],
        labels={
            'component_1': f'Principal Component 1 ({explained_variance[0]:.2%} variance)',
            'component_2': f'Principal Component 2 ({explained_variance[1]:.2%} variance)',
            color_column: color_title
        },
        title='Interactive Wallet Clusters Visualization'
    )
    
    fig.add_annotation(
        xref='paper', yref='paper',
        x=0.5, y=-0.15,
        text=f'Total variance explained: {total_variance:.2f}%',
        showarrow=False
    )
    
    fig.write_html(html_path)
    print(f"Interactive visualization saved to {html_path}")
    
    csv_path = Path(str(output_path).replace('.png', '_clusters.csv'))
    viz_df.to_csv(csv_path, index=False)
    print(f"Cluster assignments saved to {csv_path}")
    
    plt.show()
    
    return viz_df

def get_optimal_clusters(scaled_data, max_clusters=15):
    print("Determining optimal number of clusters...")
    inertia_values = []
    
    for k in range(1, max_clusters + 1):
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(scaled_data)
        inertia_values.append(kmeans.inertia_)
    
    plt.figure(figsize=(10, 6))
    plt.plot(range(1, max_clusters + 1), inertia_values, marker='o')
    plt.title('Elbow Method For Optimal k')
    plt.xlabel('Number of clusters (k)')
    plt.ylabel('Inertia')
    plt.grid(True, alpha=0.3)
    
    elbow_path = "elbow_method.png"
    plt.savefig(elbow_path)
    print(f"Elbow method plot saved to {elbow_path}")
    
    elbow_df = pd.DataFrame({
        'k': range(1, max_clusters + 1),
        'inertia': inertia_values
    })
    
    base_path = Path(__file__).parent.parent.absolute()
    html_path = base_path / "elbow_method_interactive.html"
    
    fig = px.line(
        elbow_df, 
        x='k', 
        y='inertia', 
        markers=True,
        labels={
            'k': 'Number of clusters (k)',
            'inertia': 'Inertia'
        },
        title='Interactive Elbow Method For Optimal k'
    )
    
    fig.write_html(str(html_path))
    print(f"Interactive elbow method visualization saved to {html_path}")

    deltas = np.diff(inertia_values)
    delta_of_deltas = np.diff(deltas)
    elbow_idx = np.argmax(delta_of_deltas) + 1
    optimal_k = elbow_idx + 1
    
    return optimal_k, inertia_values

def create_dash_app(df_with_clusters, viz_df, cluster_stats, inertia_values):
    print("Setting up Dash application...")
    app = dash.Dash(__name__, 
                   external_stylesheets=[
                       'https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css'
                   ])
    
    explained_variance = None
    color_column = 'target' if 'target' in viz_df.columns else 'cluster'
    if 'component_1' in viz_df.columns and 'component_2' in viz_df.columns:
        pca = PCA(n_components=2)
        pca.fit(StandardScaler().fit_transform(df_with_clusters.drop(color_column, axis=1)))
        explained_variance = pca.explained_variance_ratio_
    
    color_title = 'Target' if color_column == 'target' else 'Cluster'
    
    scatter_fig = px.scatter(
        viz_df,
        x='component_1',
        y='component_2',
        color=color_column,
        hover_data=['wallet_address'],
        labels={
            'component_1': f'PC1',
            'component_2': f'PC2',
            color_column: color_title
        },
        title='Wallet Clusters Visualization'
    )
    
    elbow_fig = px.line(
        x=list(range(1, len(inertia_values) + 1)),
        y=inertia_values,
        markers=True,
        labels={'x': 'Number of clusters (k)', 'y': 'Inertia'},
        title='Elbow Method For Optimal k'
    )
    
    numeric_features = df_with_clusters.select_dtypes(include=[np.number]).columns.tolist()
    if 'cluster' in numeric_features:
        numeric_features.remove('cluster')
    
    app.layout = html.Div([
        html.Div([
            html.H1("Wallet Clustering Analysis Dashboard", className="text-center my-4"),
            
            dcc.Tabs([
                dcc.Tab(label="Cluster Visualization", children=[
                    html.Div([
                        html.H3("Wallet Clusters in 2D Space", className="text-center my-3"),
                        dcc.Graph(figure=scatter_fig)
                    ], className="container")
                ]),
                
                dcc.Tab(label="Elbow Method", children=[
                    html.Div([
                        html.H3("Elbow Method for Optimal Clusters", className="text-center my-3"),
                        dcc.Graph(figure=elbow_fig)
                    ], className="container")
                ]),
                
                dcc.Tab(label="Feature Analysis", children=[
                    html.Div([
                        html.H3("Feature Distribution by Cluster", className="text-center my-3"),
                        html.Div([
                            html.Label("Select Feature:"),
                            dcc.Dropdown(
                                id='feature-dropdown',
                                options=[{'label': feature, 'value': feature} for feature in numeric_features],
                                value=numeric_features[0] if numeric_features else None
                            ),
                        ], className="mb-4"),
                        dcc.Graph(id='feature-distribution-plot')
                    ], className="container")
                ]),
                
                dcc.Tab(label="Cluster Statistics", children=[
                    html.Div([
                        html.H3("Cluster Summary Statistics", className="text-center my-3"),
                        html.Div(id='cluster-stats-cards', className="row")
                    ], className="container")
                ])
            ])
        ], className="container-fluid")
    ])
    
    @app.callback(
        Output('feature-distribution-plot', 'figure'),
        [Input('feature-dropdown', 'value')]
    )
    def update_feature_plot(feature):
        if not feature:
            return px.scatter(title="No feature selected")
        
        if 'target' in df_with_clusters.columns:
            fig = px.box(
                df_with_clusters, 
                x='cluster', 
                y=feature, 
                title=f'Distribution of {feature} by Cluster',
                color='target'
            )
        else:
            fig = px.box(
                df_with_clusters, 
                x='cluster', 
                y=feature, 
                title=f'Distribution of {feature} by Cluster',
                color='cluster'
            )
        return fig
    
    @app.callback(
        Output('cluster-stats-cards', 'children'),
        [Input('tabs', 'value')]
    )
    def generate_cluster_stats_cards(_):
        cards = []
        for cluster_name, data in cluster_stats.items():
            table_rows = []
            for feature, value in data['stats'].items():
                value_str = f"{value:.4f}" if isinstance(value, float) else str(value)
                table_rows.append(html.Tr([
                    html.Td(feature),
                    html.Td(value_str)
                ]))
            
            card = html.Div([
                html.Div([
                    html.H4(f"{cluster_name} ({data['count']} wallets)", className="card-title"),
                    html.Table([
                        html.Thead(html.Tr([
                            html.Th("Feature"), 
                            html.Th("Average Value")
                        ])),
                        html.Tbody(table_rows)
                    ], className="table table-striped")
                ], className="card-body")
            ], className="card col-md-6 mb-4")
            
            cards.append(card)
        
        return cards
    
    return app

def main():
    base_path = Path(__file__).parent.parent.absolute()
    json_file_path = base_path / "wn.json"
    output_path = base_path / "wallet_clusters.png"
    
    df = load_wallet_data(json_file_path)
    wallet_addresses = df.index.tolist()
    
    target = df['target'] if 'target' in df.columns else None
    
    features_for_scaling = df.drop('target', axis=1, errors='ignore')
    scaled_data, _ = scale_features(features_for_scaling)
    
    optimal_k, inertia_values = get_optimal_clusters(scaled_data)
    print(f"Suggested optimal number of clusters: {optimal_k}")
    
    n_clusters = optimal_k
    
    cluster_labels = cluster_wallets(scaled_data, n_clusters)
    
    viz_df = visualize_clusters(scaled_data, cluster_labels, wallet_addresses, output_path, df)
    
    print("\nCluster summary statistics:")
    df['cluster'] = cluster_labels
    
    cluster_stats = {}
    
    for cluster in range(n_clusters):
        cluster_df = df[df['cluster'] == cluster]
        print(f"\nCluster {cluster} ({len(cluster_df)} wallets):")
        
        stats_df = cluster_df.drop(['cluster', 'target'], axis=1, errors='ignore')
            
        stats = stats_df.mean().to_string()
        print(stats)
        
        cluster_stats[f"Cluster {cluster}"] = {
            "count": len(cluster_df),
            "stats": stats_df.mean().to_dict()
        }

    try:
        app = create_dash_app(df, viz_df, cluster_stats, inertia_values)
        
        port = 8050
        
        def open_browser():
            webbrowser.open_new(f"http://localhost:{port}")
        
        Timer(1, open_browser).start()
        
        print(f"Starting dashboard on http://localhost:{port} - Press Ctrl+C to exit")
        app.run(debug=True, port=port)
    
    except Exception as e:
        print(f"Failed to create visualization: {e}")
    
    return df, cluster_labels, viz_df

if __name__ == "__main__":
    main()
