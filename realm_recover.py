from util import *
from objects import FileHeader, ObjectParser
import mmap
import argparse


class RealmRecover(FileHeader):
    def __init__(self, filename):
        self._filename = filename
        self.used_offsets = set()

    def __enter__(self):
        self._f = open(self._filename, "rb")
        self._buf = mmap.mmap(self._f.fileno(), 0, access=mmap.ACCESS_READ)
        super().__init__(self._buf, 0x0)
        return self

    def __exit__(self, type, value, traceback):
        self._buf.close()
        self._f.close()

    def parse_objects(self, tree_root_offset):
        # [2:]하는 이유는 pk, metadata 정보는 필요 없다고 판단하여 삭제
        obj = ObjectParser(self._buf, tree_root_offset, self.used_offsets).parse_object()
        tableInformation = ObjectParser(self._buf, obj[0], self.used_offsets).parse_object()[2:]
        table_array_offsets = ObjectParser(self._buf, obj[1], self.used_offsets).parse_object()

        # obj 변수에서 사용하지 않은 나머지 offset들 털어내기
        for i in obj[2:]:
            try:
                ObjectParser(self._buf, i, self.used_offsets, recursive=1).parse_object()
            except ValueError as e:
                # print(e)
                pass


        # table_array_offsets 변수에서 사용하지 않은 나머지 offset들 털어내기
        for i in table_array_offsets[:2]:
            try:
                ObjectParser(self._buf, i, self.used_offsets, recursive=1).parse_object()
            except ValueError as e:
                # print(e)
                pass

        self.used_offsets.add(tree_root_offset)

        tables = []
        for offset in table_array_offsets[2:]:
            tableArray = ObjectParser(self._buf, offset, self.used_offsets).parse_object()
            if len(tableArray) != 2:  # Table Schema, Data Storage 고정
                raise ValueError(f"Invalid table object length: {len(tableArray)}. Expected value is 2.")
            
            table_schema_offset, data_storage_offset = tableArray
            # parse_column_type 함수 주석 참고
            aa = ObjectParser(self._buf, table_schema_offset, self.used_offsets).parse_object()

            tableSchema = [
                ObjectParser(self._buf, aa[0], self.used_offsets).parse_column_type(),  # column_type offset
                ObjectParser(self._buf, aa[1], self.used_offsets).parse_column_name(),  # column_name offset
            ]
            # aa 변수에서 사용하지 않은 나머지 offset들 털어내기
            for i in aa[2:]:
                try:
                    ObjectParser(self._buf, i, self.used_offsets, recursive=1).parse_object()
                except ValueError as e:
                    # print(e)
                    pass

            dataStorage = ObjectParser(self._buf, data_storage_offset, self.used_offsets, recursive=1).parse_object()

            tables.append([tableSchema, dataStorage])

        return tableInformation, tables

    def compare_objects(self, obj1, obj2):
        table_info1, tables1 = obj1
        table_info2, tables2 = obj2

        f = open("compare_objects.txt", "w", encoding="utf-8-sig")
        f2 = open("data_storages.txt", "w", encoding="utf-8-sig")

        if table_info1 == table_info2:
            f.write(f"[*] Table Information 일치\n")
            f.write(f"  - {table_info1}\n\n")
        else:
            f.write(f"[*] Table Information 불일치\n")
            f.write(f"  - TreeRootOffset01: {table_info1}\n")
            f.write(f"  - TreeRootOffset02: {table_info2}\n\n")

        if len(tables1) == len(tables2):
            f.write(f"[*] Table 개수 일치 - {len(tables1)}개\n\n")
        else:
            f.write(f"[*] Table 개수 불일치 - {len(tables1)}개 != {len(tables2)}개\n\n")

        for idx, (i, j) in enumerate(zip(tables1, tables2), start=1):
            table_schema1, data_storage1 = i
            table_schema2, data_storage2 = j

            if table_schema1 == table_schema2:
                f.write(f"[*] {idx}번째 Table Schema 일치\n")
                f.write(f"  - Table {idx} Schema: {table_schema1}\n\n")
            else:
                f.write(f"[*] {idx}번째 Table Schema 불일치\n")
                f.write(f"  - Table {idx} Schema1: {table_schema1}\n")
                f.write(f"  - Table {idx} Schema2: {table_schema2}\n\n")

            if data_storage1 == data_storage2:
                f.write(f"[*] {idx}번째 Table Data Storage 일치\n\n")
            else:
                f.write(f"[*] {idx}번째 Table Data Storage 불일치\n")

                for i2, j2 in zip(data_storage1, data_storage2):
                    result = ordered_difference(i2, j2)
                    f.write(f"  - TreRootOffset01에 있으나 TreRootOffset02에 없는 데이터: {result[0]}\n")
                    f.write(f"  - TreRootOffset02에 있으나 TreRootOffset01에 없는 데이터: {result[1]}\n\n")

            f2.write(f"Table {idx} Data Storage1: {data_storage1}\n\n")
            f2.write(f"Table {idx} Data Storage2: {data_storage2}\n\n")

        f.close()
        f2.close()

    def scan_all_objects(self, used_offsets):
        offsets = self._scan_for_signature()
        all_objects = []
        unused_objects = []
        for offset in offsets:
            if offset in used_offsets:
                try:
                    parser = ObjectParser(self._buf, offset)
                    if parser.object_type not in {0x45, 0x46, 0x65, 0x66}:
                        obj = parser.parse_object()
                        all_objects.append((offset, parser.object_type, parser.c, obj))
                except ValueError as e:
                    # print(e)
                    pass

                continue

            try:
                parser = ObjectParser(self._buf, offset)
                if parser.object_type not in {0x45, 0x46, 0x65, 0x66}:
                    obj = parser.parse_object()
                    unused_objects.append((offset, parser.object_type, parser.c, obj))
                    all_objects.append((offset, parser.object_type, parser.c, obj))
            except ValueError as e:
                # print(e)
                pass

        with open("scan_all_objects.txt", "w", encoding="utf-8-sig") as f:
            for offset, obj_type, obj_count, obj in all_objects:
                f.write(f"Offset: {hex(offset)}, Type: {hex(obj_type)}, Count: {obj_count}, Object: {obj}\n")

        with open("scan_unused_objects.txt", "w", encoding="utf-8-sig") as f:
            for offset, obj_type, obj_count, obj in unused_objects:
                f.write(f"Offset: {hex(offset)}, Type: {hex(obj_type)}, Count: {obj_count}, Object: {obj}\n")

    def _scan_for_signature(self, signature=b"AAAA"):
        self._buf.seek(0)
        offsets = []
        while True:
            offset = self._buf.find(signature)
            if offset == -1:
                break
            offsets.append(offset)
            self._buf.seek(offset + 1)
        return offsets


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RealmDB Recovery Tool")
    parser.add_argument("--file", help="filepath", required=True)
    args = parser.parse_args()

    with RealmRecover(args.file) as r:
        obj1 = r.parse_objects(r.treeRootOffset01)
        obj1_used_offsets = r.used_offsets

        r.used_offsets = set()

        obj2 = r.parse_objects(r.treeRootOffset02)
        obj2_used_offsets = r.used_offsets
        
        r.compare_objects(obj1, obj2)
        r.scan_all_objects(obj1_used_offsets | obj2_used_offsets)
