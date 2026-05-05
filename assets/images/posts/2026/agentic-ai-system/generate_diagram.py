"""Generate Article 7 diagram — single complete flow."""

import os
os.chdir("/tmp")

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.ml import Bedrock
from diagrams.aws.compute import Lambda
from diagrams.aws.general import User

STYLE = {
    "graph_attr": {"bgcolor": "white", "fontname": "Helvetica", "pad": "0.5"},
    "node_attr": {"fontname": "Helvetica"},
    "edge_attr": {"color": "#232F3E", "penwidth": "2.0"},
}

with Diagram("", show=False, direction="TB", filename="article-7-architecture", **STYLE):

    customer = User("Customer")
    supervisor = Bedrock("Supervisor Agent\n(Claude)")

    with Cluster("Specialist Agents"):
        order = Lambda("Order Agent\ntrack / cancel / history")
        billing = Lambda("Billing Agent\ncheck payment / refund")
        account = Lambda("Account Agent\nreset pw / update info")

    human = User("Human Review")
    response = User("Response")

    customer >> supervisor
    supervisor >> order
    supervisor >> billing
    supervisor >> account
    order >> response
    billing >> response
    account >> response
    order >> Edge(style="dashed", label="if needed") >> human
    billing >> Edge(style="dashed", label="if needed") >> human
