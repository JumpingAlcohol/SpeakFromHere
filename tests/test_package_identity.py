"""Package identity boundary tests: fake only the external kernel API calls."""
import ctypes
from ctypes import wintypes
import os
from pathlib import PureWindowsPath
import sys
import unittest

from chat_reader import windows_context


class KernelFixture:
    handle = 0x123456789
    full_name = "OpenAI.Codex_26.928.4866.0_x64__2p2nqsd0c76g0"
    family = "OpenAI.Codex_2p2nqsd0c76g0"
    root = r"C:\Registered\Codex"
    image = root + r"\app\ChatGPT.exe"

    def __init__(self, *, failure=None):
        self.failure = failure
        self.closed = []
        # Plain functions support ctypes argtypes/restype attributes.
        self.OpenProcess = lambda access, inherit, pid: (
            self.handle if access == 0x1000 and not inherit and pid == 123 else 0)
        self.CloseHandle = lambda handle: self.closed.append(handle) or True
        self.QueryFullProcessImageNameW = lambda *args: self.image_query(*args)
        self.GetPackageFamilyName = self.package_query("family", self.family)
        self.GetPackageFullName = self.package_query("full", self.full_name)
        self.GetPackagePathByFullName = self.package_query("root", self.root)

    def image_query(self, handle, flags, buffer, size):
        if handle != self.handle or flags != 0 or self.failure == "image":
            return False
        buffer.value = self.image
        return True

    def package_query(self, field, value):
        def query(owner, address, buffer):
            if owner != (self.full_name if field == "root" else self.handle):
                return 5
            if self.failure == field:
                return 5
            if self.failure == "no-package" and field == "family":
                return 15700
            size = ctypes.cast(address, ctypes.POINTER(wintypes.DWORD)).contents
            if buffer is None:
                size.value = 40000 if self.failure == "oversize" else len(value) + 1
                return 122
            if self.failure == "fill" and field == "full":
                return 122
            buffer.value = value
            size.value = len(value) + 1
            return 0
        return query


class PackageIdentityTests(unittest.TestCase):
    def query(self, kernel, pid=123):
        query = getattr(windows_context, "process_identity", None)
        self.assertTrue(callable(query), "OS-backed process package identity is missing")
        return query(pid, kernel32=kernel)

    def test_reads_package_membership_from_the_same_open_process_handle(self):
        """Wrong buffer/handle/full-name arguments prevent complete identity verification."""
        kernel = KernelFixture()
        identity = self.query(kernel)
        self.assertEqual((r"C:\Registered\Codex\app\ChatGPT.exe",
                          "OpenAI.Codex_2p2nqsd0c76g0",
                          "OpenAI.Codex_26.928.4866.0_x64__2p2nqsd0c76g0",
                          r"C:\Registered\Codex"),
                         (identity.image_path, identity.package_family,
                          identity.package_full_name, identity.package_path))
        self.assertEqual([0x123456789], kernel.closed)

    def test_unpackaged_process_has_no_trusted_membership_even_if_named_chatgpt(self):
        kernel = KernelFixture(failure="no-package")
        identity = self.query(kernel)
        self.assertEqual((None, None, None),
                         (identity.package_family, identity.package_full_name, identity.package_path))
        self.assertEqual([0x123456789], kernel.closed)

    def test_failed_or_incomplete_queries_close_the_handle_without_returning_identity(self):
        for failure in ("image", "family", "full", "root", "fill", "oversize"):
            kernel = KernelFixture(failure=failure)
            with self.subTest(failure=failure), self.assertRaises(OSError):
                self.query(kernel)
            self.assertEqual([0x123456789], kernel.closed)

    def test_failed_open_never_queries_or_closes_an_invalid_handle(self):
        kernel = KernelFixture()
        with self.assertRaises(OSError):
            self.query(kernel, pid=456)
        self.assertEqual([], kernel.closed)

    def test_package_query_failure_retains_the_api_stage_and_windows_error_code(self):
        """Replacing all API failures with one generic string hides GUI-only causes."""
        for failure, stage in (("family", "GetPackageFamilyName"),
                               ("full", "GetPackageFullName"),
                               ("root", "GetPackagePathByFullName")):
            with self.subTest(failure=failure), self.assertRaises(OSError) as raised:
                self.query(KernelFixture(failure=failure))
            self.assertIn(stage, str(raised.exception))
            self.assertIn("Windows error 5", str(raised.exception))

    def test_native_unpacked_test_process_is_not_given_a_package_identity(self):
        query = getattr(windows_context, "process_identity", None)
        self.assertTrue(callable(query), "Native package identity query is missing")
        identity = query(os.getpid())
        self.assertEqual(PureWindowsPath(sys._base_executable), PureWindowsPath(identity.image_path))
        self.assertIsNone(identity.package_family)
