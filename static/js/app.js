/* =============================================================
   ARCHIVO: static/js/app.js
   DESCRIPCIÓN: Lógica principal de la aplicación (Tienda, Admin, Auth)
   ============================================================= */

const API_URL = "http://127.0.0.1:5000/api";

document.addEventListener("DOMContentLoaded", () => {
    /* =============================================================
       0. DETECCIÓN DE PÁGINA
       ============================================================= */
    if (document.getElementById("contenedor-productos")) {
        cargarProductosTienda();
    }
    
    if (document.getElementById("tabla-productos-admin")) {
        cargarTablaAdmin();
        configurarFormularioAdmin();
    }

    /* =============================================================
       3. CONMUTACIÓN ENTRE LOGIN Y REGISTRO (authModal)
       ============================================================= */
    const goToRegister = document.getElementById('goToRegister');
    const goToLogin = document.getElementById('goToLogin');
    const registerTab = document.getElementById('register-tab');
    const loginTab = document.getElementById('login-tab');

    if (goToRegister && registerTab) {
        goToRegister.addEventListener('click', function(e) {
            e.preventDefault();
            const tab = new bootstrap.Tab(registerTab);
            tab.show();
        });
    }

    if (goToLogin && loginTab) {
        goToLogin.addEventListener('click', function(e) {
            e.preventDefault();
            const tab = new bootstrap.Tab(loginTab);
            tab.show();
        });
    }

    /* =============================================================
       4. TOGGLE DE CONTRASEÑA (Mostrar / Ocultar con el ojo)
       ============================================================= */
    const toggleButtons = document.querySelectorAll('.btn-toggle-password');

    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const passwordInput = document.getElementById(targetId);
            const icon = this.querySelector('i');

            if (!passwordInput || !icon) return;

            if (passwordInput.type === 'password') {
                passwordInput.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
            } else {
                passwordInput.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
            }
        });
    });

    /* =============================================================
       5. VALIDACIÓN EN TIEMPO REAL DE LA CONTRASEÑA (Registro)
       ============================================================= */
    const regPasswordInput = document.getElementById('reg-password');

    if (regPasswordInput) {
        regPasswordInput.addEventListener('input', function() {
            const val = this.value;

            // Pautas de validación Regex
            const hasLength = val.length >= 8;
            const hasUpper = /[A-Z]/.test(val);
            const hasLower = /[a-z]/.test(val);
            const hasNum = /[0-9]/.test(val);
            const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(val);

            // Actualizar interfaz visual
            actualizarRequisito('req-length', hasLength, "Mínimo 8 caracteres");
            actualizarRequisito('req-uppercase', hasUpper, "Una mayúscula");
            actualizarRequisito('req-lowercase', hasLower, "Una minúscula");
            actualizarRequisito('req-number', hasNum, "Un número");
            actualizarRequisito('req-special', hasSpecial, "Un símbolo (!@#$)"); // Corregido el texto
        });
    }

    function actualizarRequisito(id, esValido, texto) {
        const el = document.getElementById(id);
        if (!el) return;
        if (esValido) {
            el.className = 'text-success fw-bold';
            el.textContent = '✔ ' + texto;
        } else {
            el.className = 'text-muted';
            el.textContent = '✖ ' + texto;
        }
    }

    /* =============================================================
       6. FORMULARIO DE REGISTRO (AJAX) - CORREGIDO
       ============================================================= */
    const formRegister = document.getElementById('form-register');
    if (formRegister) {
        formRegister.addEventListener('submit', function(e) {
            e.preventDefault();

            // --- CORRECCIÓN AQUÍ: Búsqueda robusta de inputs ---
            // Buscamos por tipo (email, tel) y por placeholder para el nombre.
            // Para las contraseñas, usamos querySelectorAll('input[type="password"]').
            
            const nombreInput = formRegister.querySelector('input[placeholder*="Nombre"]') || formRegister.querySelector('input[type="text"]');
            const emailInput = formRegister.querySelector('input[type="email"]');
            const telInput = formRegister.querySelector('input[type="tel"]');
            const passInputs = formRegister.querySelectorAll('input[type="password"]');

            const nombre = nombreInput ? nombreInput.value.trim() : '';
            const email = emailInput ? emailInput.value.trim() : '';
            const telefono = telInput ? telInput.value.trim() : '';
            
            // Validamos que existan los inputs de contraseña antes de acceder
            const password = passInputs.length > 0 ? passInputs[0].value : '';
            const confirmPassword = passInputs.length > 1 ? passInputs[1].value : '';

            // Validación en JavaScript
            if (!nombre || !email || !password) {
                alert('Por favor completa todos los campos.');
                return;
            }

            if (password !== confirmPassword) {
                alert('Las contraseñas no coinciden.');
                return;
            }

            // Petición al servidor
            fetch('/api/registro', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    nombre: nombre, 
                    email: email, 
                    correo: email, // Enviamos ambos por si el backend espera uno u otro
                    telefono: telefono, 
                    password: password 
                })
            })
            .then(res => res.json())
            .then(data => {
                if (data.ok) {
                    window.location.assign(data.redirect);
                } else {
                    alert('Error: ' + (data.mensaje || 'Error desconocido'));
                }
            })
            .catch(err => {
                console.error('Error:', err);
                alert('Ocurrió un error al enviar el formulario.');
            });
        });
    }

    /* =============================================================
       7. FORMULARIO DE LOGIN (AJAX) - CORREGIDO
       ============================================================= */
    const formLogin = document.getElementById('form-login');
    if (formLogin) {
        formLogin.addEventListener('submit', function(e) {
            e.preventDefault();

            // --- CORRECCIÓN AQUÍ: Búsqueda robusta ---
            const emailInput = formLogin.querySelector('input[type="email"]');
            const passInput = formLogin.querySelector('input[type="password"]');

            const email = emailInput ? emailInput.value.trim() : '';
            const password = passInput ? passInput.value : '';

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
            .then(res => res.json())
            .then(data => {
                if (data.ok) {
                    window.location.assign(data.redirect);
                } else {
                    alert('Error: ' + (data.mensaje || 'Credenciales incorrectas'));
                }
            })
            .catch(err => {
                console.error('Error:', err);
                alert('Error al iniciar sesión');
            });
        });
    }
});

/* =============================================================
   1. FUNCIONES PARA LA TIENDA (index.html)
   ============================================================= */

async function cargarProductosTienda() {
    const contenedor = document.getElementById("contenedor-productos");

    try {
        const respuesta = await fetch(`${API_URL}/productos`);
        const datos = await respuesta.json();

        if (!datos.ok || !datos.productos || datos.productos.length === 0) {
            mostrarProductosDemo(contenedor);
            return;
        }

        renderizarProductosTienda(datos.productos, contenedor);
    } catch (error) {
        console.warn("API no detectada o error de red. Cargando vista previa estática...", error);
        mostrarProductosDemo(contenedor);
    }
}

function renderizarProductosTienda(productos, contenedor) {
    contenedor.innerHTML = "";
    productos.forEach(prod => {
        contenedor.innerHTML += `
            <div class="col-md-3">
                <div class="card h-100 shadow-sm border-0">
                    <img src="${prod.imagen_url || 'https://images.unsplash.com/photo-1621996346565-e3d5d6288365?q=80&w=400'}" class="card-img-top rounded-top" style="height: 180px; object-fit: cover;" alt="${prod.nombre}">
                    <div class="card-body d-flex flex-column justify-content-between">
                        <div>
                            <h6 class="fw-bold mb-1">${prod.nombre}</h6>
                            <p class="small text-muted mb-2">${prod.descripcion || ''}</p>
                        </div>
                        <div class="d-flex justify-content-between align-items-center mt-2">
                            <span class="fw-bold text-cafe">$${parseFloat(prod.precio).toFixed(2)}</span>
                            <button class="btn btn-sm btn-outline-dark rounded-circle" onclick="agregarAlCarrito(${prod.id_producto})">
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
        { id_producto: 1, nombre: "Pastelito de queso", descripcion: "Relleno de rico queso de la casa congelado listo para freír", precio: 0.50, imagen_url: "https://images.unsplash.com/photo-1621996346565-e3d5d6288365?q=80&w=400" },
        { id_producto: 2, nombre: "Pastelito de pollo", descripcion: "Delicioso relleno de pollo sazonado con el secreto de la abuela", precio: 0.50, imagen_url: "https://images.unsplash.com/photo-1621996346565-e3d5d6288365?q=80&w=400" },
        { id_producto: 3, nombre: "Calzone", descripcion: "Deliciosa masa rellena del queso, salsa y relleno de su elección", precio: 3.50, imagen_url: "https://images.unsplash.com/photo-1534308983496-4fabb1a015ee?q=80&w=400" },
        { id_producto: 4, nombre: "Pizza", descripcion: "Deliciosa pizza artesanal hecha con ingredientes frescos", precio: 7.00, imagen_url: "https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=400" }
    ];
    renderizarProductosTienda(productosDemo, contenedor);
}

function agregarAlCarrito(idProducto) {
    alert(`Producto #${idProducto} agregado al carrito de compras.`);
}

/* =============================================================
   2. FUNCIONES PARA EL PANEL DE ADMINISTRACIÓN (admin.html)
   ============================================================= */

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
        console.error("Error al cargar productos en el panel admin:", error);
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