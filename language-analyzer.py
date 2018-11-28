#!/usr/bin/env python3

"""
 Example Analyser gRPC service implementation.
 Posts file-level comments for every file with language detected.
"""

from concurrent.futures import ThreadPoolExecutor

import time
import grpc

from lookout.sdk import AnalyzerServicer, add_analyzer_to_server
from lookout.sdk import service_analyzer_pb2
from lookout.sdk import service_data_pb2_grpc
from lookout.sdk import service_data_pb2
from lookout.sdk.grpc import to_grpc_address, create_channel

from bblfsh import filter as filter_uast

port_to_listen = 2021
data_srv_addr = to_grpc_address("ipv4://localhost:10301")
version = "alpha"


class Analyzer(AnalyzerServicer):
    def NotifyReviewEvent(self, request, context):
        print("got review request {}".format(request))

        # client connection to DataServe
        channel = create_channel(data_srv_addr)
        stub = service_data_pb2_grpc.DataStub(channel)
        changes = stub.GetChanges(
            service_data_pb2.ChangesRequest(
                head=request.commit_revision.head,
                base=request.commit_revision.base,
                want_contents=False,
                want_uast=True,
                exclude_vendored=True))

        comments = []
        for change in changes:
            if not change.HasField("head"):
                continue

            print("analyzing '{}' in {}".format(
                change.head.path, change.head.language))
            fns = list(filter_uast(change.head.uast, "//*[@roleFunction]"))
            comments.append(
                service_analyzer_pb2.Comment(
                    file=change.head.path,
                    line=0,
                    text="language: {}, functions: {}".format(change.head.language, len(fns))))
        return service_analyzer_pb2.EventResponse(analyzer_version=version, comments=comments)

    def NotifyPushEvent(self, request, context):
        pass


def serve():
    server = grpc.server(thread_pool=ThreadPoolExecutor(max_workers=10))
    add_analyzer_to_server(Analyzer(), server)
    server.add_insecure_port("0.0.0.0:{}".format(port_to_listen))
    server.start()

    one_day_sec = 60 * 60 * 24
    try:
        while True:
            time.sleep(one_day_sec)
    except KeyboardInterrupt:
        server.stop(0)


def main():
    print("starting gRPC Analyzer server at port {}".format(port_to_listen))
    serve()


if __name__ == "__main__":
    main()
