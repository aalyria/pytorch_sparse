from typing import List

import torch
from torch_sparse.storage import SparseStorage
from torch_sparse.tensor import SparseTensor


@torch.jit.script
def cat(tensors: List[SparseTensor], dim: int) -> SparseTensor:
    assert len(tensors) > 0
    if dim < 0:
        dim = tensors[0].dim() + dim

    if dim == 0:
        rows: List[torch.Tensor] = []
        rowptrs: List[torch.Tensor] = []
        cols: List[torch.Tensor] = []
        values: List[torch.Tensor] = []
        sparse_sizes: List[int] = [0, 0]
        rowcounts: List[torch.Tensor] = []

        nnz: int = 0
        for tensor in tensors:
            row = tensor.storage._row
            if row is not None:
                rows.append(row + sparse_sizes[0])

            rowptr = tensor.storage._rowptr
            if rowptr is not None:
                if len(rowptrs) > 0:
                    rowptr = rowptr[1:]
                rowptrs.append(rowptr + nnz)

            cols.append(tensor.storage._col)

            value = tensor.storage._value
            if value is not None:
                values.append(value)

            rowcount = tensor.storage._rowcount
            if rowcount is not None:
                rowcounts.append(rowcount)

            sparse_sizes[0] += tensor.sparse_size(0)
            sparse_sizes[1] = max(sparse_sizes[1], tensor.sparse_size(1))
            nnz += tensor.nnz()

        row: Optional[torch.Tensor] = None
        if len(rows) == len(tensors):
            row = torch.cat(rows, dim=0)

        rowptr: Optional[torch.Tensor] = None
        if len(rowptrs) == len(tensors):
            rowptr = torch.cat(rowptrs, dim=0)

        col = torch.cat(cols, dim=0)

        value: Optional[torch.Tensor] = None
        if len(values) == len(tensors):
            value = torch.cat(values, dim=0)

        rowcount: Optional[torch.Tensor] = None
        if len(rowcounts) == len(tensors):
            rowcount = torch.cat(rowcounts, dim=0)

        storage = SparseStorage(
            row=row,
            rowptr=rowptr,
            col=col,
            value=value,
            sparse_sizes=sparse_sizes,
            rowcount=rowcount,
            colptr=None,
            colcount=None,
            csr2csc=None,
            csc2csr=None,
            is_sorted=True)
        return tensors[0].from_storage(storage)

    elif dim == 1:
        rows: List[torch.Tensor] = []
        cols: List[torch.Tensor] = []
        values: List[torch.Tensor] = []
        sparse_sizes: List[int] = [0, 0]
        colptrs: List[torch.Tensor] = []
        colcounts: List[torch.Tensor] = []

        nnz: int = 0
        for tensor in tensors:
            row, col, value = tensor.coo()

            rows.append(row)

            cols.append(tensor.storage._col + sparse_sizes[1])

            if value is not None:
                values.append(value)

            colptr = tensor.storage._colptr
            if colptr is not None:
                if len(colptrs) > 0:
                    colptr = colptr[1:]
                colptrs.append(colptr + nnz)

            colcount = tensor.storage._colcount
            if colcount is not None:
                colcounts.append(colcount)

            sparse_sizes[0] = max(sparse_sizes[0], tensor.sparse_size(0))
            sparse_sizes[1] += tensor.sparse_size(1)
            nnz += tensor.nnz()

        row = torch.cat(rows, dim=0)

        col = torch.cat(cols, dim=0)

        value: Optional[torch.Tensor] = None
        if len(values) == len(tensors):
            value = torch.cat(values, dim=0)

        colptr: Optional[torch.Tensor] = None
        if len(colptrs) == len(tensors):
            colptr = torch.cat(colptrs, dim=0)

        colcount: Optional[torch.Tensor] = None
        if len(colcounts) == len(tensors):
            colcount = torch.cat(colcounts, dim=0)

        storage = SparseStorage(
            row=row,
            rowptr=None,
            col=col,
            value=value,
            sparse_sizes=sparse_sizes,
            rowcount=None,
            colptr=colptr,
            colcount=colcount,
            csr2csc=None,
            csc2csr=None,
            is_sorted=False)
        return tensors[0].from_storage(storage)

    elif dim > 1 and dim < tensors[0].dim():
        values: List[torch.Tensor] = []
        for tensor in tensors:
            value = tensor.storage.value()
            if value is not None:
                values.append(value)

        value: Optional[torch.Tensor] = None
        if len(values) == len(tensors):
            value = torch.cat(values, dim=dim - 1)

        return tensors[0].set_value(value, layout='coo')
    else:
        raise IndexError(
            f'Dimension out of range: Expected to be in range of '
            '[{-tensors[0].dim()}, {tensors[0].dim() - 1}], but got {dim}.')


@torch.jit.script
def cat_diag(tensors: List[SparseTensor]) -> SparseTensor:
    assert len(tensors) > 0

    rows: List[torch.Tensor] = []
    rowptrs: List[torch.Tensor] = []
    cols: List[torch.Tensor] = []
    values: List[torch.Tensor] = []
    sparse_sizes: List[int] = [0, 0]
    rowcounts: List[torch.Tensor] = []
    colptrs: List[torch.Tensor] = []
    colcounts: List[torch.Tensor] = []
    csr2cscs: List[torch.Tensor] = []
    csc2csrs: List[torch.Tensor] = []

    nnz: int = 0
    for tensor in tensors:
        row = tensor.storage._row
        if row is not None:
            rows.append(row + sparse_sizes[0])

        rowptr = tensor.storage._rowptr
        if rowptr is not None:
            if len(rowptrs) > 0:
                rowptr = rowptr[1:]
            rowptrs.append(rowptr + nnz)

        cols.append(tensor.storage._col + sparse_sizes[1])

        value = tensor.storage._value
        if value is not None:
            values.append(value)

        rowcount = tensor.storage._rowcount
        if rowcount is not None:
            rowcounts.append(rowcount)

        colptr = tensor.storage._colptr
        if colptr is not None:
            if len(colptrs) > 0:
                colptr = colptr[1:]
            colptrs.append(colptr + nnz)

        colcount = tensor.storage._colcount
        if colcount is not None:
            colcounts.append(colcount)

        csr2csc = tensor.storage._csr2csc
        if csr2csc is not None:
            csr2cscs.append(csr2csc + nnz)

        csc2csr = tensor.storage._csc2csr
        if csc2csr is not None:
            csc2csrs.append(csc2csr + nnz)

        sparse_sizes[0] += tensor.sparse_size(0)
        sparse_sizes[1] += tensor.sparse_size(1)
        nnz += tensor.nnz()

    row: Optional[torch.Tensor] = None
    if len(rows) == len(tensors):
        row = torch.cat(rows, dim=0)

    rowptr: Optional[torch.Tensor] = None
    if len(rowptrs) == len(tensors):
        rowptr = torch.cat(rowptrs, dim=0)

    col = torch.cat(cols, dim=0)

    value: Optional[torch.Tensor] = None
    if len(values) == len(tensors):
        value = torch.cat(values, dim=0)

    rowcount: Optional[torch.Tensor] = None
    if len(rowcounts) == len(tensors):
        rowcount = torch.cat(rowcounts, dim=0)

    colptr: Optional[torch.Tensor] = None
    if len(colptrs) == len(tensors):
        colptr = torch.cat(colptrs, dim=0)

    colcount: Optional[torch.Tensor] = None
    if len(colcounts) == len(tensors):
        colcount = torch.cat(colcounts, dim=0)

    csr2csc: Optional[torch.Tensor] = None
    if len(csr2cscs) == len(tensors):
        csr2csc = torch.cat(csr2cscs, dim=0)

    csc2csr: Optional[torch.Tensor] = None
    if len(csc2csrs) == len(tensors):
        csc2csr = torch.cat(csc2csrs, dim=0)

    storage = SparseStorage(
        row=row,
        rowptr=rowptr,
        col=col,
        value=value,
        sparse_sizes=sparse_sizes,
        rowcount=rowcount,
        colptr=colptr,
        colcount=colcount,
        csr2csc=csr2csc,
        csc2csr=csc2csr,
        is_sorted=True)
    return tensors[0].from_storage(storage)
