import lldb


class OdinSliceSyntheticProvider:
    def __init__(self, valobj, internal_dict):
        self.valobj = valobj
        self._data_ptr = None
        self._length = 0
        self._element_type = None
        self._element_size = 0

    def num_children(self):
        return self._length

    def get_child_index(self, name):
        try:
            return int(name.lstrip("[").rstrip("]"))
        except ValueError:
            return -1

    def get_child_at_index(self, index):
        if index < 0 or index >= self._length:
            return None
        if self._data_ptr is None or self._element_type is None:
            return None

        offset = index * self._element_size
        addr = self._data_ptr + offset
        return self.valobj.CreateValueFromAddress(
            f"[{index}]", addr, self._element_type
        )

    def update(self):
        self._data_ptr = None
        self._length = 0
        self._element_type = None
        self._element_size = 0

        try:
            data = self.valobj.GetChildMemberWithName("data")
            length = self.valobj.GetChildMemberWithName("len")

            if not data.IsValid() or not length.IsValid():
                return

            self._length = length.GetValueAsUnsigned(0)
            self._data_ptr = data.GetValueAsUnsigned(0)

            if self._data_ptr == 0:
                self._length = 0
                return

            ptr_type = data.GetType()
            if ptr_type.IsPointerType():
                self._element_type = ptr_type.GetPointeeType()
                self._element_size = self._element_type.GetByteSize()

            # cap the number of children to avoid performance issues
            self._length = min(self._length, 1000)

        except Exception:
            pass

    def has_children(self):
        return self._length > 0


class OdinDynamicArraySyntheticProvider(OdinSliceSyntheticProvider):
    pass


def odin_string_summary(valobj, internal_dict):
    try:
        data = valobj.GetChildMemberWithName("data")
        length = valobj.GetChildMemberWithName("len")

        if not data.IsValid() or not length.IsValid():
            return None

        len_val = length.GetValueAsUnsigned(0)
        if len_val == 0:
            return '""'

        # limit display length
        display_len = min(len_val, 256)

        data_addr = data.GetValueAsUnsigned(0)
        if data_addr == 0:
            return "<nil>"

        error = lldb.SBError()
        process = valobj.GetProcess()
        content = process.ReadMemory(data_addr, display_len, error)

        if error.Fail():
            return None

        try:
            text = content.decode("utf-8", errors="replace")
        except Exception:
            text = repr(content)

        if len_val > display_len:
            return f'"{text}..." (len={len_val})'
        return f'"{text}"'

    except Exception:
        return None


def odin_slice_summary(valobj, internal_dict):
    try:
        valobj = valobj.GetNonSyntheticValue()
        data = valobj.GetChildMemberWithName("data")
        length = valobj.GetChildMemberWithName("len")

        if not data.IsValid() or not length.IsValid():
            return None

        len_val = length.GetValueAsUnsigned(0)
        data_addr = data.GetValueAsUnsigned(0)

        if data_addr == 0 and len_val == 0:
            return "[] (len=0)"
        if data_addr == 0:
            return f"<nil> (len={len_val})"

        return f"len={len_val}"

    except Exception:
        return None


def odin_dynamic_array_summary(valobj, internal_dict):
    try:
        valobj = valobj.GetNonSyntheticValue()
        data = valobj.GetChildMemberWithName("data")
        length = valobj.GetChildMemberWithName("len")
        cap = valobj.GetChildMemberWithName("cap")

        if not data.IsValid() or not length.IsValid():
            return None

        len_val = length.GetValueAsUnsigned(0)
        cap_val = cap.GetValueAsUnsigned(0) if cap.IsValid() else 0
        data_addr = data.GetValueAsUnsigned(0)

        if data_addr == 0 and len_val == 0:
            return f"[] (len=0, cap={cap_val})"
        if data_addr == 0:
            return f"<nil> (len={len_val}, cap={cap_val})"

        return f"len={len_val}, cap={cap_val}"

    except Exception:
        return None


def __lldb_init_module(debugger, internal_dict):
    debugger.HandleCommand(
        'type summary add -F odin_lldb.odin_string_summary "string" -w odin'
    )

    debugger.HandleCommand(
        'type summary add -x "^\\[\\].+" -F odin_lldb.odin_slice_summary -w odin'
    )
    debugger.HandleCommand(
        'type synthetic add -x "^\\[\\].+" -l odin_lldb.OdinSliceSyntheticProvider -w odin'
    )

    debugger.HandleCommand(
        'type summary add -x "^\\[dynamic\\].+" -F odin_lldb.odin_dynamic_array_summary -w odin'
    )
    debugger.HandleCommand(
        'type synthetic add -x "^\\[dynamic\\].+" -l odin_lldb.OdinDynamicArraySyntheticProvider -w odin'
    )

    debugger.HandleCommand("type category enable odin")

    print("Odin LLDB formatters loaded.")
