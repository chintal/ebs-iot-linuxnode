

from . import BaseShellMixin


class WifiNetworkInfoMixin(BaseShellMixin):

    @property
    def wifi_ssid(self):
        def _handle_result(result):
            return result.strip()
        d = self._shell_execute(['iwgetid', '-s'], _handle_result)
        return d


class NetworkInfoMixin(WifiNetworkInfoMixin):

    @property
    def network_info(self):
        return self.wifi_ssid
