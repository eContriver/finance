#  Copyright 2021-2022 eContriver LLC
#  This file is part of Finance from eContriver.
#
#  Finance from eContriver is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  any later version.
#
#  Finance from eContriver is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with Finance from eContriver.  If not, see <https://www.gnu.org/licenses/>.

from enum import Enum


class UnknownWalletTypeException(RuntimeError):
    """
    When a wallet type is requested which is not supported this exception is thrown.
    """
    pass


class WalletType(Enum):
    """
    WalletType: indicates if the wallet was set up with write capabilities (general private key access)
    """
    NO_WALLET = 'no wallet'
    READ_ONLY = 'read-only'
    WRITE_CAPABLE = 'write-capable'


class Wallet:
    wallet_type: WalletType = WalletType.NO_WALLET

    def __init__(self, address: str, private: str):
        self.wallet_type = WalletType.WRITE_CAPABLE if private else WalletType.READ_ONLY
        self.address = address
        self.private = private
