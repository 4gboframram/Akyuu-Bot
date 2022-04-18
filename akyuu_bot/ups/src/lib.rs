use pyo3::prelude::*;
use pyo3::types::PyBytes;
use flips::UpsPatch;
use flips::Error as FlipsError;
use pyo3::create_exception;

create_exception!(ups_wrapper, PatchError, pyo3::exceptions::PyException);

fn convert_err<T>(err: Result<T, FlipsError>) -> PyResult<T> {
    err.map_err(|x| { PatchError::new_err(format!("{}", x))})
}

#[pyclass(name="UpsPatch")]
#[derive(Debug, Clone)]
struct PyUpsPatch {
    _patch: UpsPatch<Box<[u8]>>
}



#[pymethods]
impl PyUpsPatch {
    #[new]
    fn new<'a>(patch: &'a PyBytes) -> Self {
        // Were only allowing bytes to prevent copying
        PyUpsPatch {
            _patch: UpsPatch::new(patch.as_bytes().into())
        }
    }

    pub fn apply<'py>(&'py self, py: Python<'py>, source: &'py PyBytes) -> PyResult<&'py PyBytes> {
        let patched = convert_err(self._patch.apply(source.as_bytes()))?;
        let out = patched.as_bytes();
        Ok(PyBytes::new(py, out))
    }
}

/// A Python module implemented in Rust. The name of this function must match
/// the `lib.name` setting in the `Cargo.toml`, else Python will not be able to
/// import the module.


#[pymodule]
fn ups_wrapper(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyUpsPatch>()?;
    m.add("PatchError", py.get_type::<PatchError>())?;
    Ok(())
}