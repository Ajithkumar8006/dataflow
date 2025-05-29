import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions


def run():
    # Hardcoded values
    PROJECT_ID = "apigee-test-0001-demo"  # 🔁 Replace with your actual GCP project ID
    TOPIC_NAME = "test-topic"  # 🔁 Replace with your actual topic name

    INPUT_TOPIC = f"projects/{PROJECT_ID}/topics/{TOPIC_NAME}"

    pipeline_options = PipelineOptions()
    pipeline_options.view_as(StandardOptions).streaming = True

    with beam.Pipeline(options=pipeline_options) as p:
        (
            p
            | 'ReadFromPubSub' >> beam.io.ReadFromPubSub(
                topic=INPUT_TOPIC
            ).with_output_types(bytes)
            | 'DecodeMessage' >> beam.Map(lambda x: x.decode('utf-8'))
            | 'PrintToConsole' >> beam.Map(print)
        )


if __name__ == '__main__':
    run()
