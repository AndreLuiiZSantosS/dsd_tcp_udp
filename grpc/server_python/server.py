import os
import sys
import time
import grpc
from concurrent import futures
from typing import TYPE_CHECKING

# Ensure generated gRPC Python modules are available. If not, try to generate them
# from the .proto file using grpc_tools.protoc. This makes running the server
# easier for development without a separate generation step.
try:
    import chat_pb2
    import chat_pb2_grpc
except Exception:
    proto_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'proto'))
    proto_file = os.path.join(proto_dir, 'chat.proto')
    out_dir = os.path.dirname(__file__)
    try:
        from grpc_tools import protoc
    except Exception:
        raise ImportError(
            'grpc_tools is required to auto-generate gRPC stubs. Install with: pip install grpcio-tools'
        )

    args = [
        'protoc',
        f'-I{proto_dir}',
        f'--python_out={out_dir}',
        f'--grpc_python_out={out_dir}',
        proto_file,
    ]
    if protoc.main(args) != 0:
        raise RuntimeError('protoc failed to generate Python gRPC files')

    # Ensure the generated files are importable from this package
    sys.path.insert(0, out_dir)
    import chat_pb2
    import chat_pb2_grpc


users = []


class UserService(chat_pb2_grpc.UserServiceServicer):
    def Login(self, request, context):
        if request.username not in users:
            users.append(request.username)
        return chat_pb2.UserReply(message='Usuário logado')

    def ListUsers(self, request, context):
        return chat_pb2.UserList(users=users)


def serve(port: int = 6000):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_UserServiceServicer_to_server(UserService(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Servidor gRPC Python rodando na porta {port}")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        print('Encerrando servidor...')
        server.stop(0)


if __name__ == '__main__':
    serve()
