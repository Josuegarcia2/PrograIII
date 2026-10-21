
async function hacerLogin() {
    const usuario = document.getElementById('login-usuario').value;
    const clave = document.getElementById('login-clave').value;
    
    const res = await fetch('/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({usuario, clave})
    });
    
    const data = await res.json();
    if (data.success) {
        window.location.href = data.redirect;
    } else {
        document.getElementById('msj-login').innerText = data.mensaje;
    }
}


async function guardarUsuario() {
    const id = document.getElementById('edit-id').value;
    const datos = {
        usuario: document.getElementById('usuario').value,
        clave: document.getElementById('clave').value,
        nombre: document.getElementById('nombre').value,
        direccion: document.getElementById('direccion').value,
        telefono: document.getElementById('telefono').value
    };
    
    const url = id ? `/api/editar/${id}` : '/api/guardar';
    const metodo = id ? 'PUT' : 'POST';

    const res = await fetch(url, {
        method: metodo,
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(datos)
    });
    
    if (res.ok) {
        limpiarFormulario();
        buscarUsuarios();
    }
}

async function buscarUsuarios() {
    const q = document.getElementById('busqueda').value;
    const res = await fetch(`/api/buscar?q=${q}`);
    const usuarios = await res.json();
    
    const tbody = document.getElementById('tabla-usuarios');
    tbody.innerHTML = '';
    
    usuarios.forEach(u => {
        
        tbody.innerHTML += `
            <tr>
                <td>${u.idUsuario}</td>
                <td>${u.usuario}</td>
                <td>${u.nombre}</td>
                <td>${u['dirección'] || ''}</td>
                <td>${u['teléfono'] || ''}</td>
                <td>
                    <button onclick="prepararEdicion(${u.idUsuario}, '${u.usuario}', '${u.clave}', '${u.nombre}', '${u['dirección'] || ''}', '${u['teléfono'] || ''}')">Editar</button>
                    <button onclick="eliminarUsuario(${u.idUsuario})" style="background:red;">Eliminar</button>
                </td>
            </tr>
        `;
    });
}

async function eliminarUsuario(id) {
    if (!confirm('¿Seguro que desea eliminar este usuario?')) return;
    await fetch(`/api/eliminar/${id}`, { method: 'DELETE' });
    buscarUsuarios();
}

function prepararEdicion(id, usuario, clave, nombre, direccion, telefono) {
    document.getElementById('edit-id').value = id;
    document.getElementById('usuario').value = usuario;
    document.getElementById('clave').value = clave;
    document.getElementById('nombre').value = nombre;
    document.getElementById('direccion').value = direccion;
    document.getElementById('telefono').value = telefono;
    
    document.getElementById('btn-cancelar').classList.remove('oculto');
}

function limpiarFormulario() {
    document.getElementById('edit-id').value = '';
    document.getElementById('usuario').value = '';
    document.getElementById('clave').value = '';
    document.getElementById('nombre').value = '';
    document.getElementById('direccion').value = '';
    document.getElementById('telefono').value = '';
    document.getElementById('btn-cancelar').classList.add('oculto');
}


if (document.getElementById('vista-sistema') && !document.getElementById('vista-sistema').classList.contains('oculto')) {
    buscarUsuarios();
}