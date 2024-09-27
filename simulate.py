import argparse

parser = argparse.ArgumentParser(description="Script to run Gem5 ACA Simulations")

parser.add_argument('--pipeline-width', type=int, help="Number of reorder buffer entries.")
parser.add_argument('--rob-size', type=int, help="Number of reorder buffer entries.")
parser.add_argument('--iq-size', type=int, help="Number of instruction queue entries.")
parser.add_argument('--lq-size', type=int, help="Number of load queue entries.")
parser.add_argument('--sq-size', type=int, help="Number of store queue entries.")
