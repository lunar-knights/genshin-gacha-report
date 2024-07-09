import stat
import traceback
import os

import paramiko

from Product.MARP.digital_verification.src.infrastructure.server.file.file_server import FileServer
from Product.MARP.digital_verification.src.infrastructure.server.file.confg import FILE_SERVER_CFG


class SFTPFileServer(FileServer):
    def __init__(self):
        sftp_cfg = FILE_SERVER_CFG["SFTP"]
        self._repository_root_path = sftp_cfg["repository_root_path"]
        try:
            _t = paramiko.Transport((sftp_cfg["ip"], sftp_cfg["port"]))
            _t.connect(username=sftp_cfg["username"], password=sftp_cfg["password"])
            self._sftp = paramiko.SFTPClient.from_transport(_t)
        except Exception as e:
            print(f"connect to %s time out" % sftp_cfg["ip"])
            raise Exception(traceback.format_exc()) from e

    def upload(self, local_path, remote_dir_relate_path) -> None:
        remote_path = os.path.join(self._repository_root_path, remote_dir_relate_path, os.path.basename(local_path)).replace("\\", "/")

        if not os.path.exists(local_path):
            raise Exception("upload path: %s not exists" % local_path)

        self.__remote_mkdirs(remote_dir_relate_path)

        if os.path.isfile(local_path):
            self._sftp.put(local_path, remote_path)
        elif os.path.isdir(local_path):
            try:
                self._sftp.chdir(remote_path)
            except:
                self._sftp.mkdir(remote_path)
            self._sftp.chdir("/")
            for sub_path in os.listdir(local_path):
                self.upload(os.path.join(local_path, sub_path), remote_path.replace(self._repository_root_path + "/", ""))

    def __remote_mkdirs(self, remote_relate_path: str):
        sub_path_list = remote_relate_path.split("/")
        test_path = self._repository_root_path
        for sub_path in sub_path_list:
            test_path = test_path + "/" + sub_path
            try:
                self._sftp.chdir(test_path)
            except:
                self._sftp.mkdir(test_path)
            self._sftp.chdir("/")

    def download(self, local_dir_path, remote_relate_path) -> None:
        remote_path_real = os.path.join(self._repository_root_path, remote_relate_path).replace("\\", "/")
        local_path_real = os.path.join(local_dir_path, os.path.basename(remote_path_real))

        if not os.path.isdir(local_dir_path):
            os.makedirs(local_dir_path)

        if stat.S_ISDIR(self._sftp.stat(remote_path_real).st_mode):
            for sub_path in self._sftp.listdir(remote_path_real):
                remote_path_tmp = os.path.join(remote_path_real, sub_path).replace("\\", "/")
                local_file_tmp = os.path.join(local_path_real, sub_path)

                if stat.S_ISDIR(self._sftp.stat(remote_path_tmp).st_mode):
                    self.download(local_path_real, remote_path_tmp.replace(self._repository_root_path + "/", ""))
                else:
                    if not os.path.isdir(local_path_real):
                        os.makedirs(local_path_real)
                    self._sftp.get(remote_path_tmp, local_file_tmp)
        else:
            self._sftp.get(remote_path_real, local_path_real)

    def close(self):
        self._sftp.close()
