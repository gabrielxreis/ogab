import{r as f}from"./vendor-react-CXr8A1Q2.js";import"./vendor-ui-BmDwtkP-.js";var c={exports:{}},i={};/**
 * @license React
 * use-sync-external-store-shim.production.js
 *
 * Copyright (c) Meta Platforms, Inc. and affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */var u=f;function S(e,t){return e===t&&(e!==0||1/e===1/t)||e!==e&&t!==t}var p=typeof Object.is=="function"?Object.is:S,d=u.useState,l=u.useEffect,v=u.useLayoutEffect,E=u.useDebugValue;function m(e,t){var r=t(),o=d({inst:{value:r,getSnapshot:t}}),n=o[0].inst,a=o[1];return v(function(){n.value=r,n.getSnapshot=t,s(n)&&a({inst:n})},[e,r,t]),l(function(){return s(n)&&a({inst:n}),e(function(){s(n)&&a({inst:n})})},[e]),E(r),r}function s(e){var t=e.getSnapshot;e=e.value;try{var r=t();return!p(e,r)}catch{return!0}}function y(e,t){return t()}var h=typeof window>"u"||typeof window.document>"u"||typeof window.document.createElement>"u"?y:m;i.useSyncExternalStore=u.useSyncExternalStore!==void 0?u.useSyncExternalStore:h;c.exports=i;var b=c.exports;export{b as s};
