from util import *
import struct


class COLUMN_TYPE:
    Integer = 0x0
    Bool = 0x1
    String = 0x2
    Binary = 0x4
    Table = 0x5
    Mixed = 0x6
    OldDateTime = 0x7
    Timestamp = 0x8
    Float = 0x9
    Double = 0xA
    Link = 0xC
    LinkList = 0xD


COLUMN_TYPE_MAP = {
    value: name
    for name, value in vars(COLUMN_TYPE).items()
    if not name.startswith("__")
}


def get_column_type(flag):
    return COLUMN_TYPE_MAP.get(flag, "Unknown")


# class COLUMN_OPTION:
#     PrimaryKey = 0x01
#     EnableNullValue = 0x10


class ObjectParser:
    def __init__(self, buf, offset, recursive=0):
        self._buf = buf
        self._buf.seek(offset)
        self._valid_signature()
        self.recursive = recursive

        self.object_type = byte_to_int(self._buf.read(2))
        self.c = int.from_bytes(self._buf.read(2))  # length or count

    # parse_object 규칙에 맞지 않는 경우가 있어서 따로 분리
    # ex: column name 가져올 때 object type이 0xc인데 string인 경우가 있었다.
    # table schema에는 column type, column name 데이터가 고정이기 때문
    def parse_column_name(self):
        return self._parse_string()

    def parse_column_type(self):
        column_type_flag = byte_to_int(self._buf.read(8))
        return [
            get_column_type((column_type_flag >> i) & 0xF)
            for i in range(0, column_type_flag.bit_length(), 4)
        ]

    def parse_object(self):
        parser_method = {
            0x1: self._parse_boolean,
            0x4: self._parse_int8,
            0x5: self._parse_int16,
            0x6: self._parse_int32,  # Timestamp, 테이블의 index 참조에도 쓰인다.
            0x7: self._parse_int64,
            0xB: self._parse_float,
            0xC: self._parse_double,
            0xD: self._parse_string,
            0xE: self._parse_string,
            0x11: self._parse_string2,
            0x45: self._parse_realm_object_45,
            0x46: self._parse_realm_object_46,
            0x65: self._parse_realm_object_65,
            0x66: self._parse_realm_object_66,
        }.get(self.object_type)

        if parser_method:
            return parser_method()
        else:
            raise ValueError(f"Unknown object type: {hex(self.object_type)}")

    def _parse_boolean(self):
        bool_flag = read_boolean(self._buf)
        binary_string = bin(byte_to_int(bool_flag))[2:]
        return [bit == "1" for bit in reversed(binary_string)]

    def _parse_int8(self):
        return [byte_to_int(self._buf.read(1)) for _ in range(self.c)]

    def _parse_int16(self):
        return [byte_to_int(self._buf.read(2)) for _ in range(self.c)]

    def _parse_int32(self):
        value = [byte_to_int(self._buf.read(4)) for _ in range(self.c)]
        # timestamp인 경우 0x7FFFFFFF으로 시작한다.
        if len(value) > 1 and value[0] == 0x7FFFFFFF:
            return [num_to_timestamp(i) for i in value[1:]]

        return value

    def _parse_int64(self):
        return [byte_to_int(self._buf.read(8)) for _ in range(self.c)]

    def _parse_float(self):
        return [struct.unpack("f", self._buf.read(4))[0] for _ in range(self.c)]

    def _parse_double(self):
        return [struct.unpack("d", self._buf.read(8))[0] for _ in range(self.c)]

    def _parse_string(self):
        return [read_string(self._buf) for _ in range(self.c)]

    def _parse_string2(self):
        data = self._buf.read(self.c).rstrip(b"\x00")
        if data.count(b"\x00") > 0:
            return data.split(b"\x00")
        return data

    def _parse_realm_object_recursive(self, sub_offsets):
        result = []
        for sub_offset in sub_offsets:
            parser = ObjectParser(self._buf, sub_offset, self.recursive)
            try:
                result.append(parser.parse_object())
            except ValueError as e:
                # 0x3, 0x43 등 Unknown Object Type인 경우 pass
                pass

        return result

    def _parse_realm_object_45(self):
        sub_offsets = [byte_to_int(self._buf.read(2)) for _ in range(self.c)]

        if self.recursive == 1:
            return self._parse_realm_object_recursive(sub_offsets)

        return sub_offsets

    def _parse_realm_object_46(self):
        sub_offsets = [byte_to_int(self._buf.read(4)) for _ in range(self.c)]

        if self.recursive == 1:
            return self._parse_realm_object_recursive(sub_offsets)

        return sub_offsets

    def _parse_realm_object_65(self):
        sub_offsets = [byte_to_int(self._buf.read(2)) for _ in range(self.c)]

        if self.recursive == 1:
            return self._parse_realm_object_recursive(sub_offsets)

        return sub_offsets

    def _parse_realm_object_66(self):
        sub_offsets = [byte_to_int(self._buf.read(4)) for _ in range(self.c)]

        if self.recursive == 1:
            return self._parse_realm_object_recursive(sub_offsets)

        return sub_offsets

    def _valid_signature(self):
        sig = self._buf.read(4)
        if sig != b"AAAA":
            raise ValueError(f"Unexpected Signature value. {sig} != AAAA")


class FileHeader:
    def __init__(self, buf, offset):
        self._buf = buf
        self._buf.seek(offset)
        self.treeRootOffset01 = byte_to_int(self._buf.read(8))
        self.treeRootOffset02 = byte_to_int(self._buf.read(8))
        self.fileSignature = self._buf.read(8)
        self.check_magic()
        self.treeRootOffset = self.get_tree_root_offset()

    def check_magic(self):
        if not self.fileSignature.startswith(b"T-DB"):
            raise ValueError(f"Unexpected magic value. {self.fileSignature} != T-DB")

    def get_tree_root_offset(self):
        self.tree_root_flag = self.fileSignature[-1]

        if self.tree_root_flag == 0x00:
            return self.treeRootOffset01
        elif self.tree_root_flag == 0x01:
            return self.treeRootOffset02
        else:
            raise ValueError(f"Unexpected fileSignature[-1] value: {self.tree_root_flag}. Expected value is 0x00 or 0x01.")
