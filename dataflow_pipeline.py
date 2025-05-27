import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions

options = PipelineOptions(
    streaming=True,
    project='your-project-id',
    region='us-central1',
    job_name='pubsub-test-job',
    temp_location='gs://your-bucket/tmp',
    runner='DataflowRunner'
)

with beam.Pipeline(options=options) as p:
    (p
     | 'ReadFromPubSub' >> beam.io.ReadFromPubSub(topic='projects/your-project-id/topics/test-topic')
     | 'Decode' >> beam.Map(lambda x: x.decode('utf-8'))
     | 'Log' >> beam.Map(print)
    )
