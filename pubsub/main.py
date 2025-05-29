import argparse
import json
import logging
import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions


class ParseMessage(beam.DoFn):
    def process(self, element):
        try:
            record = json.loads(element.decode('utf-8'))
            logging.info(f"Parsed message: {record}")
            yield record
        except json.JSONDecodeError:
            logging.warning("Could not decode JSON")
            return


def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_topic', required=True, help='Input Pub/Sub topic')
    known_args, pipeline_args = parser.parse_known_args(argv)

    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(StandardOptions).streaming = True

    with beam.Pipeline(options=pipeline_options) as p:
        (
            p
            | 'ReadFromPubSub' >> beam.io.ReadFromPubSub(topic=known_args.input_topic)
            | 'ParseJSON' >> beam.ParDo(ParseMessage())
            | 'LogOutput' >> beam.Map(logging.info)
        )


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    run()
