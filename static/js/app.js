const API_URL = "/api";

document.addEventListener("DOMContentLoaded", () => {

    
    if (document.getElementById("contenedor-productos")) {
        cargarProductosTienda();
    }
    if (document.getElementById("tabla-productos-admin")) {
        cargarTablaAdmin();
        configurarFormularioAdmin();
    }

   
    const goToRegister = document.getElementById('goToRegister');
    const goToLogin    = document.getElementById('goToLogin');
    const registerTab  = document.getElementById('register-tab');
    const loginTab     = document.getElementById('login-tab');

    if (goToRegister && registerTab) {
        goToRegister.addEventListener('click', (e) => {
            e.preventDefault();
            new bootstrap.Tab(registerTab).show();
        });
    }
    if (goToLogin && loginTab) {
        goToLogin.addEventListener('click', (e) => {
            e.preventDefault();
            new bootstrap.Tab(loginTab).show();
        });
    }

   
    document.querySelectorAll('.btn-toggle-password').forEach((btn) => {
        btn.addEventListener('click', function () {
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            const icon  = this.querySelector('i');
            if (!input || !icon) return;

            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });

    
    const regPassInput = document.getElementById('reg-password');
    if (regPassInput) {
        regPassInput.addEventListener('input', function () {
            const val = this.value;
            actualizarRequisito('req-length',    val.length >= 8,                    "Mínimo 8 caracteres");
            actualizarRequisito('req-uppercase', /[A-Z]/.test(val),                   "Una mayúscula");
            actualizarRequisito('req-lowercase', /[a-z]/.test(val),                   "Una minúscula");
            actualizarRequisito('req-number',    /[0-9]/.test(val),                   "Un número");
            actualizarRequisito('req-special',   /[!@#$%^&*(),.?":{}|<>]/.test(val),  "Un símbolo (!@#$)");
        });
    }

    function actualizarRequisito(id, ok, texto) {
        const el = document.getElementById(id);
        if (!el) return;
        if (ok) {
            el.className = 'text-success fw-bold';
            el.textContent = '✔ ' + texto;
        } else {
            el.className = 'text-muted';
            el.textContent = '✖ ' + texto;
        }
    }

  
    const formRegister = document.getElementById('form-register');
    if (formRegister) {
        formRegister.addEventListener('submit', function (e) {
            e.preventDefault();

            const nombreInput = formRegister.querySelector('input[placeholder*="Nombre"]') || formRegister.querySelector('input[type="text"]');
            const emailInput  = formRegister.querySelector('input[type="email"]');
            const telInput    = formRegister.querySelector('input[type="tel"]');
            const passInputs  = formRegister.querySelectorAll('input[type="password"]');

            const nombre = nombreInput ? nombreInput.value.trim() : '';
            const email  = emailInput  ? emailInput.value.trim()  : '';
            const telefono = telInput  ? telInput.value.trim()    : '';
            const password        = passInputs.length > 0 ? passInputs[0].value : '';
            const confirmPassword = passInputs.length > 1 ? passInputs[1].value : '';

            if (!nombre || !email || !password) {
                alert('Por favor completa todos los campos.');
                return;
            }
            if (password !== confirmPassword) {
                alert('Las contraseñas no coinciden.');
                return;
            }

            fetch('/api/registro', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    nombre: nombre,
                    email: email,
                    correo: email,
                    telefono: telefono,
                    password: password
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.ok) {
                    window.location.assign(data.redirect || '/cliente.html');
                } else {
                    alert('Error: ' + (data.mensaje || 'Error desconocido'));
                }
            })
            .catch(err => {
                console.error('Error registro:', err);
                alert('No se pudo conectar con el servidor.');
            });
        });
    }

   
    const formLogin = document.getElementById('form-login');
    if (formLogin) {
        formLogin.addEventListener('submit', function (e) {
            e.preventDefault();

            const emailInput = formLogin.querySelector('input[type="email"]');
            const passInput  = formLogin.querySelector('input[type="password"]');

            const email    = emailInput ? emailInput.value.trim() : '';
            const password = passInput  ? passInput.value         : '';

            if (!email || !password) {
                alert('Por favor ingresa tu correo y contraseña.');
                return;
            }

            fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: email,
                    correo: email,
                    password: password
                })
            })
            .then(res => {
              
                return res.json().then(body => ({ status: res.status, body }));
            })
            .then(({ status, body }) => {
                if (body && body.ok) {
                    window.location.assign(body.redirect || '/cliente.html');
                } else {
                    alert('Error: ' + (body?.mensaje || 'Credenciales incorrectas'));
                }
            })
            .catch(err => {
                console.error('Error login:', err);
                alert('No se pudo conectar con el servidor.');
            });
        });
    }

   
    const btnOpenChat  = document.getElementById('btn-open-chat');
    const btnCloseChat = document.getElementById('btn-close-chat');
    const modalChat    = document.getElementById('modal-chat-ia');
    const btnSendChat  = document.getElementById('btn-send-chat');
    const inputChatMsg = document.getElementById('input-chat-msg');
    const boxMessages  = document.getElementById('chat-messages');

    if (btnOpenChat && modalChat) {
        btnOpenChat.addEventListener('click', () => modalChat.classList.toggle('d-none'));
    }
    if (btnCloseChat && modalChat) {
        btnCloseChat.addEventListener('click', () => modalChat.classList.add('d-none'));
    }

    function procesarMensajeChat(texto) {
        if (!texto || !boxMessages) return;

        boxMessages.innerHTML += `
            <div class="bg-dark text-white p-2 rounded-3 align-self-end ms-auto shadow-sm" style="max-width: 85%;">
                ${texto}
            </div>
        `;
        boxMessages.scrollTop = boxMessages.scrollHeight;

        fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mensaje: texto })
        })
        .then(res => res.json())
        .then(data => {
            const resp = (data && data.respuesta) ? data.respuesta : 'Ocurrió un error.';
            boxMessages.innerHTML += `
                <div class="bg-white p-2 rounded-3 text-dark align-self-start border shadow-sm" style="max-width: 85%;">
                    ${resp.replace(/\n/g, '<br>')}
                </div>
            `;
            boxMessages.scrollTop = boxMessages.scrollHeight;
        })
        .catch(() => {
            boxMessages.innerHTML += `<div class="text-danger small align-self-start">Error de conexión.</div>`;
            boxMessages.scrollTop = boxMessages.scrollHeight;
        });
    }

    document.querySelectorAll('.btn-pregunta').forEach(btn => {
        btn.addEventListener('click', function () {
            procesarMensajeChat(this.getAttribute('data-texto'));
        });
    });

    if (btnSendChat && inputChatMsg) {
        btnSendChat.addEventListener('click', () => {
            const texto = inputChatMsg.value.trim();
            if (texto) { procesarMensajeChat(texto); inputChatMsg.value = ''; }
        });
        inputChatMsg.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const texto = inputChatMsg.value.trim();
                if (texto) { procesarMensajeChat(texto); inputChatMsg.value = ''; }
            }
        });
    }

});


async function cargarProductosTienda() {
    const contenedor = document.getElementById("contenedor-productos");
    if (!contenedor) return;

    try {
        const respuesta = await fetch(`${API_URL}/productos`);
        const datos = await respuesta.json();

        if (!datos.ok || !datos.productos || datos.productos.length === 0) {
            mostrarProductosDemo(contenedor);
            return;
        }
        renderizarProductosTienda(datos.productos, contenedor);
    } catch (error) {
        console.warn("API no disponible. Cargando demo...", error);
        mostrarProductosDemo(contenedor);
    }
}

function renderizarProductosTienda(productos, contenedor) {
    contenedor.innerHTML = "";
    productos.forEach(prod => {
        contenedor.innerHTML += `
            <div class="col-md-3">
                <div class="card h-100 shadow-sm border-0">
                    <img src="${prod.imagen_url || 'https://images.unsplash.com/photo-1621996346565-e3d5d6288365?q=80&w=400'}"
                         class="card-img-top rounded-top"
                         style="height: 180px; object-fit: cover;"
                         alt="${prod.nombre}">
                    <div class="card-body d-flex flex-column justify-content-between">
                        <div>
                            <h6 class="fw-bold mb-1">${prod.nombre}</h6>
                            <p class="small text-muted mb-2">${prod.descripcion || ''}</p>
                        </div>
                        <div class="d-flex justify-content-between align-items-center mt-2">
                            <span class="fw-bold text-cafe">$${parseFloat(prod.precio).toFixed(2)}</span>
                            <button class="btn btn-sm btn-outline-dark rounded-circle"
                                    onclick="agregarAlCarrito(${prod.id_producto})">
                                <i class="fa-solid fa-cart-shopping"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });
}

function mostrarProductosDemo(contenedor) {
    const productosDemo = [
        { id_producto: 1, nombre: "Pastelito de queso", descripcion: "Queso de la casa, congelado listo para freír", precio: 0.50, imagen_url: "https://images.unsplash.com/photo-1621996346565-e3d5d6288365?q=80&w=400" },
        { id_producto: 2, nombre: "Pastelito de pollo", descripcion: "Pollo sazonado con el secreto de la abuela", precio: 0.50, imagen_url: "https://images.unsplash.com/photo-1621996346565-e3d5d6288365?q=80&w=400" },
        { id_producto: 3, nombre: "Calzone", descripcion: "Masa rellena de queso y salsa", precio: 3.50, imagen_url: "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?q=80&w=400" },
        { id_producto: 4, nombre: "Pizza", descripcion: "Pizza artesanal con ingredientes frescos", precio: 7.00, imagen_url: "https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=400" }
    ];
    renderizarProductosTienda(productosDemo, contenedor);
}

function agregarAlCarrito(idProducto) {
    alert(`Producto #${idProducto} agregado al carrito.`);
}


async function cargarTablaAdmin() {
    const tbody = document.getElementById("tabla-productos-admin");
    if (!tbody) return;

    try {
        const respuesta = await fetch(`${API_URL}/productos`);
        const datos = await respuesta.json();
        tbody.innerHTML = "";

        if (datos.ok && datos.productos) {
            datos.productos.forEach(p => {
                tbody.innerHTML += `
                    <tr>
                        <td><img src="${p.imagen_url}" width="50" height="50" style="object-fit:cover;" class="rounded"></td>
                        <td><strong>${p.nombre}</strong></td>
                        <td>$${parseFloat(p.precio).toFixed(2)}</td>
                        <td>${p.stock}</td>
                    </tr>
                `;
            });
        }
    } catch (error) {
        console.error("Error al cargar productos en admin:", error);
    }
}

function configurarFormularioAdmin() {
    const form = document.getElementById("form-producto");
    if (!form) return;

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const nuevoProd = {
            nombre: document.getElementById("nombre").value,
            descripcion: document.getElementById("descripcion").value,
            precio: parseFloat(document.getElementById("precio").value),
            stock: parseInt(document.getElementById("stock").value),
            id_categoria: parseInt(document.getElementById("id_categoria").value),
            imagen_url: document.getElementById("imagen_url").value
        };

        try {
            const respuesta = await fetch(`${API_URL}/productos`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(nuevoProd)
            });
            const resultado = await respuesta.json();

            if (respuesta.ok && resultado.ok) {
                alert("Producto agregado correctamente");
                form.reset();
                cargarTablaAdmin();
            } else {
                alert("Error al guardar el producto");
            }
        } catch (error) {
            console.error("Error al enviar el producto:", error);
            alert("No se pudo conectar con el servidor backend");
        }
    });
}