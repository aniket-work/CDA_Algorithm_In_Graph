import time
import networkx as nx
from pyvis.network import Network
import webbrowser
import random
from neo4j import GraphDatabase


# Function to generate random entities
def generate_entities(num_banks, num_personal_accounts, num_social_accounts):
    entities = []
    entities.extend(['Bank' + str(i) for i in range(1, num_banks + 1)])
    entities.extend(['PersonalAccount' + str(i) for i in range(1, num_personal_accounts + 1)])
    entities.extend(['SocialAccount' + str(i) for i in range(1, num_social_accounts + 1)])
    return entities


# Function to generate random transactions
def generate_transactions(entities, num_transactions):
    transactions = []
    for _ in range(num_transactions):
        source = random.choice(entities)
        target = random.choice(entities)
        while source == target:  # Ensure source and target are different
            target = random.choice(entities)
        transaction_type = random.choice(['Credit', 'Debit'])
        amount = round(random.uniform(10, 1000), 2)  # Random amount between 10 and 1000
        transactions.append((source, target, {'transaction_type': transaction_type, 'amount': amount}))
    return transactions


# Function to create and visualize network
def create_and_visualize_network():
    # Generate entities
    num_banks = 5
    num_personal_accounts = 10
    num_social_accounts = 15
    entities = generate_entities(num_banks, num_personal_accounts, num_social_accounts)

    # Create a networkx graph
    G = nx.MultiDiGraph()

    # Add nodes
    G.add_nodes_from(entities)

    # Generate transactions
    num_transactions = 50
    transactions = generate_transactions(entities, num_transactions)

    # Add edges with transaction details
    G.add_edges_from(transactions)

    # Create a pyvis network
    network = Network(notebook=False)
    network.from_nx(G)

    # Save the graph to an HTML file
    html_file = 'financial_network.html'
    network.save_graph(html_file)
    print(f"Graph exported to '{html_file}'")

    # Open the HTML file in a web browser
    webbrowser.open_new_tab(html_file)


# Call the function to create and visualize the network
create_and_visualize_network()

from neo4j import GraphDatabase


def load_data_into_neo4j(tx, entities, transactions):
    for entity in entities:
        tx.run("CREATE (:Entity {id: $id})", id=entity)

    for source, target, transaction_details in transactions:
        tx.run("MATCH (a:Entity {id: $source}), (b:Entity {id: $target}) "
               "CREATE (a)-[r:TRANSACTION {transaction_type: $transaction_type, weight: $amount}]->(b) "
               "SET r.amount = $amount",
               source=source, target=target,
               transaction_type=transaction_details['transaction_type'],
               amount=transaction_details['amount'])

def run_louvain(tx, graph_name):  # Add graph_name as a parameter
    print("Graph name inside run_louvain:", graph_name)  # Add this line
    print("Available graphs:", tx.run("CALL gds.graph.list()").value())  # Add this line
    query = (
        f"CALL gds.louvain.mutate('{graph_name}', "  # Use the in-memory graph name
        "{ mutateProperty: 'communityId' }) YIELD communityCount, modularity, modularities"
    )
    result = tx.run(query)
    for record in result:
        print(f"Detected {record['communityCount']} communities with modularity {record['modularity']}")



def verify_projected_graph(tx):
    tx.run(" CALL gds.graph.project(  "
        "    'financial_graph', "
        "     'Entity', "
        " { "
        "       TRANSACTION: { "
        "           orientation: 'UNDIRECTED' "
        "       } "
        "   }, "
        "   {       "  
        "       relationshipProperties: 'weight' "
        "   } "
        " )").value()[0]
    graph_name = "financial_graph"
    print("Projected graph name:", graph_name)
    results = tx.run("MATCH (n)-[r:TRANSACTION]->() WHERE n.id IN ['Bank1', 'PersonalAccount2'] RETURN r LIMIT 10")  # Adjust node IDs
    for record in results:
        print(record['r']._properties)  # Access properties using '_properties'
    return graph_name



# Neo4j connection parameters
uri = "bolt://localhost:7687"
user = "neo4j"
password = "abcd1234"

# Connect to Neo4j
driver = GraphDatabase.driver(uri, auth=(user, password))
with driver.session() as session:
    # Generate entities and transactions (if you intend to do it in the script)
    entities = generate_entities(5, 10, 15)
    transactions = generate_transactions(entities, 50)

    # Load data into Neo4j
    session.execute_write(load_data_into_neo4j, entities, transactions)

    # Delete any existing projected graph
    session.run("CALL gds.graph.drop('financial_graph')")



    # Load the projected graph into memory
    graph_name = session.execute_write(verify_projected_graph)
    print("graph_name from session", graph_name)

    # Optional pause for inspection:
    time.sleep(10)

    # Run Louvain algorithm (pass the graph_name)
    session.execute_write(lambda tx: run_louvain(tx, graph_name))

# Close the Neo4j driver
driver.close()
