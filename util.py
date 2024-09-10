from datetime import datetime, timezone


def ordered_difference(list1, list2):
    if isinstance(list1, list) and isinstance(list2, list):
        diff1 = []
        diff2 = []
        for sublist1, sublist2 in zip(list1, list2):
            sub_diff1, sub_diff2 = ordered_difference(sublist1, sublist2)
            if sub_diff1 or sub_diff2:
                diff1.append(sub_diff1)
                diff2.append(sub_diff2)

        if len(list1) > len(list2):
            diff1.extend(list1[len(list2) :])
        elif len(list2) > len(list1):
            diff2.extend(list2[len(list1) :])
        return diff1, diff2
    else:
        return ([list1] if list1 != list2 else [], [list2] if list1 != list2 else [])


def byte_to_int(data):
    return int.from_bytes(data, byteorder="little")


def read_string(f):
    value = bytearray()
    while True:
        byte = f.read(1)
        if byte == b"\x00":
            break
        value.extend(byte)

    while True:
        zero_byte = f.read(1)
        if zero_byte != b"\x00":
            break

    return value


# object 구조에 맞추기 위해서 4바이트 단위로 끊고, 나머지는 0으로 채우기 때문에 4바이트씩 끊어서 AAAA 시그니처 만나기 전까지 파싱하면 될듯
# \x00으로 자르는건 안되는 이유가 있는데 byte 값 중간에 00이 있는 경우도 있음
def read_boolean(f):
    value = bytearray()
    while True:
        byte = f.read(4)
        if byte == b"AAAA":
            break
        value.extend(byte)

    return value


def num_to_timestamp(num):
    return datetime.fromtimestamp(num, tz=timezone.utc).isoformat()
