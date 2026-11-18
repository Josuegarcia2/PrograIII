const API_URL = "/api";
const IMG_POR_DEFECTO = "https://images.unsplash.com/photo-1621996346565-e3d5d6288365?q=80&w=400";

function escapeHtml(valor) {
    return String(valor ?? "")
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function rutaImagen(producto) {
    const img = producto.imagen || producto.imagen_url;
    if (!img) return IMG_POR_DEFECTO;
    if (/^https?:\/\//.test(img) || img.startsWith("/")) return img;
    return "/static/" + img;
}

document.addEventListener("DOMContentLoaded", () => {

    if (document.getElementById("contenedor-productos")) {
        cargarProductosTienda();
    }

    // ----- Cambiar entre pestañas Login / Registro -----
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

    // ----- Mostrar / ocultar contraseña (actualizado para funcionar de forma universal) -----
    document.querySelectorAll('.btn-toggle-password').forEach((btn) => {
        btn.addEventListener('click', function (e) {
            e.preventDefault();
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

    // ----- Requisitos de contraseña en vivo -----
    const regPassInput = document.getElementById('reg_password');
    if (regPassInput) {
        regPassInput.addEventListener('input', function () {
            const val = this.value;
            actualizarRequisito('req-length',    val.length >= 8,                    "Mínimo 8 caracteres");
            actualizarRequisito('req-uppercase', /[A-Z]/.test(val),                  "Una mayúscula");
            actualizarRequisito('req-lowercase', /[a-z]/.test(val),                  "Una minúscula");
            actualizarRequisito('req-number',    /[0-9]/.test(val),                  "Un número");
            actualizarRequisito('req-special',   /[^A-Za-z0-9]/.test(val),           "Un símbolo (!@#$)");
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

    // ----- Registro -----
    const formRegister = document.getElementById('form-register');
    if (formRegister) {
        formRegister.addEventListener('submit', function (e) {
            e.preventDefault();

            const nombreInput = formRegister.querySelector('input[name="nombre"]');
            const emailInput  = formRegister.querySelector('input[name="correo"]');
            const telInput    = formRegister.querySelector('input[name="telefono"]');
            const passInput   = formRegister.querySelector('input[name="password"]');
            const confirmInput = formRegister.querySelector('input[name="confirm_password"]');

            const nombre   = nombreInput ? nombreInput.value.trim() : '';
            const email    = emailInput  ? emailInput.value.trim()  : '';
            const telefono = telInput    ? telInput.value.trim()    : '';
            const password        = passInput   ? passInput.value         : '';
            const confirmPassword = confirmInput ? confirmInput.value     : '';

            if (!nombre || !email || !password || !telefono) {
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
                body: JSON.stringify({ nombre, email, correo: email, telefono, password })
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

    // ----- Login -----
    const formLogin = document.getElementById('form-login');
    if (formLogin) {
        formLogin.addEventListener('submit', function (e) {
            e.preventDefault();

            const emailInput = formLogin.querySelector('input[name="correo"]');
            const passInput  = formLogin.querySelector('input[name="password"]');
            const email    = emailInput ? emailInput.value.trim() : '';
            const password = passInput  ? passInput.value         : '';

            if (!email || !password) {
                alert('Por favor ingresa tu correo y contraseña.');
                return;
            }

            fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, correo: email, password })
            })
            .then(res => res.json())
            .then(body => {
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
    contenedor.innerHTML = productos.map(prod => `
        <div class="col-md-3">
            <div class="card h-100 shadow-sm border-0">
                <img src="${escapeHtml(rutaImagen(prod))}"
                     onerror="this.onerror=null;this.src='${IMG_POR_DEFECTO}'"
                     class="card-img-top rounded-top"
                     style="height: 180px; object-fit: cover;"
                     alt="${escapeHtml(prod.nombre)}">
                <div class="card-body d-flex flex-column justify-content-between">
                    <div>
                        <h6 class="fw-bold mb-1">${escapeHtml(prod.nombre)}</h6>
                        <p class="small text-muted mb-2">${escapeHtml(prod.descripcion || '')}</p>
                    </div>
                    <div class="d-flex justify-content-between align-items-center mt-2">
                        <span class="fw-bold text-cafe">$${parseFloat(prod.precio).toFixed(2)}</span>
                        <button class="btn btn-sm btn-outline-dark rounded-circle"
                                onclick="agregarAlCarrito()">
                            <i class="fa-solid fa-cart-shopping"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `).join("");
}

function mostrarProductosDemo(contenedor) {
    const productosDemo = [
        { nombre: "Pastelito de queso", descripcion: "Queso de la casa, congelado listo para freír", precio: 0.50, imagen: "https://images.unsplash.com/photo-1621996346565-e3d5d6288365?q=80&w=400" },
        { nombre: "Pastelito de pollo", descripcion: "Pollo sazonado con el secreto de la abuela", precio: 0.50, imagen: "https://images.unsplash.com/photo-1621996346565-e3d5d6288365?q=80&w=400" },
        { nombre: "Calzone", descripcion: "Masa rellena de queso y salsa", precio: 3.50, imagen: "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?q=80&w=400" },
        { nombre: "Pizza", descripcion: "Pizza artesanal con ingredientes frescos", precio: 7.00, imagen: "https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=400" }
    ];
    renderizarProductosTienda(productosDemo, contenedor);
}


function agregarAlCarrito() {
    const modalEl = document.getElementById('authModal');
    if (modalEl && window.bootstrap) {
        bootstrap.Modal.getOrCreateInstance(modalEl).show();
    } else {
        alert('Inicia sesión para agregar productos al carrito.');
    }
}