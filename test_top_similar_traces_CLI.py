# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

# CLI INTERFACE THAT TAKES STACK TRACE AS INPUT AND RETURNS SIMILAR STACK TRACES

import download_data
import crash_similarity
import argparse

parser = argparse.ArgumentParser(description='Returns the top ten similar stack traces')
parser.add_argument('--crash_id', required=True, help='crash_id corresponding to the stack trace')
parser.add_argument('--product', required=True, help='Product for which crash data is needed to be downloaded')
parser.add_argument('--top', help='Number of top similar and different stack traces(Default 10)', default=10, type=int)
args = parser.parse_args()

if __name__ == '__main__':
  # downloads some data (e.g. the past 7 days)
  download_data.download_crashes(days=7, product=args.product)
  paths = download_data.get_paths(days=7, product=args.product)
  
  # reads the corpus
  corpus = crash_similarity.read_corpus(paths)
  
  # trains the model on that data
  model = crash_similarity.train_model(corpus)
  
  # gets the stack_trace corresponding to the crash_id (input by the user as an argument)
  stack_trace = crash_similarity.get_stack_trace_from_crashid(args.crash_id)
  
  # returns the top similar stack traces (number of stack traces returned = args.top)
  similarities = crash_similarity.top_similar_traces(model, corpus, stack_trace, args.top)
  
  for similarity in similarities:
    print(u'%s: <%s>\n' % ((corpus[similarity[0]].tags[1], similarity[1]), ' '.join(corpus[similarity[0]].words))
