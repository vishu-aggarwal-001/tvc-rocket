// Bundled with esbuild into parts_viewer.bundle.js (see build.sh). Exposes what parts.html needs.
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { toCreasedNormals } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
window.SkyParts = { THREE, OrbitControls, RoomEnvironment, toCreasedNormals };
