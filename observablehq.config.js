// Dashboard de discriminación hacia las mujeres, con corte transversal de
// discapacidad. Cuatro fuentes (ENADIS, ENIGH, Censo 2020, ENDIREH) y tres
// comparaciones fijas: mujeres vs hombres, mujeres con vs sin discapacidad,
// y mujeres con discapacidad vs hombres con discapacidad.
// Estilo Social Data Ibero, tomado de anomalias-concesiones (custom-style.css).
import fs from "node:fs";
import path from "node:path";
import {fileURLToPath} from "node:url";

// El framework reescribe paths a assets en header/footer/head, pero NO en
// `home`; por eso el logo del sidebar se inlina crudo.
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const logoOriginalSvg = fs.readFileSync(
  path.join(__dirname, "src/images/social_data_original.svg"),
  "utf-8"
);

export default {
  title: "Discriminación y género",
  root: "src",
  style: "custom-style.css",
  toc: true,
  search: true,

  interpreters: {
    ".py": ["uv", "run", "python", "-u"],
  },

  // base hardcodeado rompe `npm run dev`; solo aplica en GitHub Actions.
  base: process.env.GITHUB_ACTIONS ? "/discriminacion-mujeres/" : "/",

  // Navegación por ENCUESTA, no por tema. Cada encuesta agrupa sus subtemas,
  // porque una cifra solo es comparable con otra de la misma fuente: los
  // universos, los años y los instrumentos difieren entre encuestas.
  // El orden es el de prioridad editorial del proyecto.
  pages: [
    // La portada NO se lista aquí: el título del sidebar ya enlaza a "/", y
    // repetirla como "Distribución" daba dos entradas al mismo destino.
    {
      name: "Censo 2020",
      open: true,
      // Numeralia y Educación se agregan en tasks posteriores de esta misma
      // ronda (docs/superpowers/plans/2026-08-29-filtros-y-censo-plan.md):
      // el nav se declara antes de que esas páginas existan a propósito.
      pages: [
        {name: "Numeralia", path: "/encuestas/censo/numeralia-censo"},
        {name: "Trabajo", path: "/encuestas/censo/trabajo-censo"},
        {name: "Educación", path: "/encuestas/censo/educacion-censo"},
      ],
    },
    {
      name: "ENIGH",
      open: true,
      pages: [
        {name: "Trabajo e ingreso", path: "/encuestas/enigh/trabajo"},
        {name: "Educación", path: "/encuestas/enigh/educacion-enigh"},
        {name: "Jefatura del hogar", path: "/encuestas/enigh/hogar"},
        {name: "Ingreso y apoyos", path: "/encuestas/enigh/ingreso"},
        {name: "Gastos por discapacidad", path: "/encuestas/enigh/gastos"},
        {name: "Tecnología y conectividad", path: "/encuestas/enigh/tecnologia"},
      ],
    },
    {
      name: "ENDIREH",
      open: true,
      pages: [
        {name: "Tipos de violencia", path: "/encuestas/endireh/autonomia"},
        {name: "Quién ejerce la violencia", path: "/encuestas/endireh/agresor"},
      ],
    },
    {
      name: "ENADIS",
      open: true,
      pages: [
        {name: "Discriminación vivida", path: "/encuestas/enadis/discriminacion"},
        {name: "Educación", path: "/encuestas/enadis/educacion"},
        {name: "Trabajo", path: "/encuestas/enadis/trabajo-enadis"},
      ],
    },
    {
      name: "Metodología",
      pages: [
        {name: "Fuentes y cobertura", path: "/metodologia/fuentes"},
        {name: "Definiciones", path: "/metodologia/definiciones"},
      ],
    },
  ],

  home: `<span class="sidebar-brand">
  <span class="sidebar-brand-logo" aria-hidden="true">${logoOriginalSvg}</span>
  <span class="sidebar-brand-text">
    <span class="sidebar-brand-title">Discriminación y género</span>
    <span class="sidebar-brand-sub">Social Data Ibero</span>
  </span>
</span>`,

  head: `<link rel="icon" href="/images/social_data_original.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<meta name="author" content="Social Data Ibero">`,

  // Sin header: solo contenía un enlace a Social Data que ya vive en el pie y
  // en la marca del sidebar, y robaba alto a las gráficas en cada página.

  footer: `<div class="book-footer">
  <div class="book-footer-grid">
    <a href="https://socialdata.ibero.mx" target="_blank" rel="noopener" class="book-footer-brand" aria-label="Social Data Ibero · Universidad Iberoamericana">
      <img src="/images/social_data_gris.svg" alt="" class="book-footer-logo">
      <span class="book-footer-brand-text">
        <span class="book-footer-name">Social Data Ibero</span>
        <span class="book-footer-inst">Universidad Iberoamericana · Ciudad de México</span>
      </span>
    </a>
    <div class="book-footer-col">
      <h4 class="book-footer-col-title">Datos</h4>
      <p class="book-footer-col-line">ENADIS 2017 y 2022 · ENIGH 2020-2024 (INEGI)</p>
      <p class="book-footer-col-line">Censo 2020, cuestionario ampliado · ENDIREH 2016 y 2021</p>
    </div>
  </div>
  <div class="book-footer-bottom">
    <span>&copy; 2026 Social Data Ibero</span>
    <span class="book-footer-tech">Construido con <a href="https://observablehq.com/framework/" target="_blank" rel="noopener">Observable Framework</a></span>
  </div>
</div>`,
};
