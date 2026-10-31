/* go-e + SteVe Smart Charging card — bundled, do not edit by hand. Source in /card. */
var _t=Object.defineProperty;var ft=Object.getOwnPropertyDescriptor;var _=(a,s,e,t)=>{for(var r=t>1?void 0:t?ft(s,e):s,i=a.length-1,n;i>=0;i--)(n=a[i])&&(r=(t?n(s,e,r):n(r))||r);return t&&r&&_t(s,e,r),r};var ue=globalThis,ge=ue.ShadowRoot&&(ue.ShadyCSS===void 0||ue.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,Ne=Symbol(),Ue=new WeakMap,re=class{constructor(s,e,t){if(this._$cssResult$=!0,t!==Ne)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=s,this.t=e}get styleSheet(){let s=this.o,e=this.t;if(ge&&s===void 0){let t=e!==void 0&&e.length===1;t&&(s=Ue.get(e)),s===void 0&&((this.o=s=new CSSStyleSheet).replaceSync(this.cssText),t&&Ue.set(e,s))}return s}toString(){return this.cssText}},Be=a=>new re(typeof a=="string"?a:a+"",void 0,Ne),S=(a,...s)=>{let e=a.length===1?a[0]:s.reduce((t,r,i)=>t+(n=>{if(n._$cssResult$===!0)return n.cssText;if(typeof n=="number")return n;throw Error("Value passed to 'css' function must be a 'css' function result: "+n+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(r)+a[i+1],a[0]);return new re(e,a,Ne)},Fe=(a,s)=>{if(ge)a.adoptedStyleSheets=s.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of s){let t=document.createElement("style"),r=ue.litNonce;r!==void 0&&t.setAttribute("nonce",r),t.textContent=e.cssText,a.appendChild(t)}},Ae=ge?a=>a:a=>a instanceof CSSStyleSheet?(s=>{let e="";for(let t of s.cssRules)e+=t.cssText;return Be(e)})(a):a;var{is:bt,defineProperty:vt,getOwnPropertyDescriptor:yt,getOwnPropertyNames:xt,getOwnPropertySymbols:wt,getPrototypeOf:$t}=Object,me=globalThis,Ve=me.trustedTypes,kt=Ve?Ve.emptyScript:"",St=me.reactiveElementPolyfillSupport,se=(a,s)=>a,ie={toAttribute(a,s){switch(s){case Boolean:a=a?kt:null;break;case Object:case Array:a=a==null?a:JSON.stringify(a)}return a},fromAttribute(a,s){let e=a;switch(s){case Boolean:e=a!==null;break;case Number:e=a===null?null:Number(a);break;case Object:case Array:try{e=JSON.parse(a)}catch{e=null}}return e}},_e=(a,s)=>!bt(a,s),qe={attribute:!0,type:String,converter:ie,reflect:!1,useDefault:!1,hasChanged:_e};Symbol.metadata??=Symbol("metadata"),me.litPropertyMetadata??=new WeakMap;var H=class extends HTMLElement{static addInitializer(s){this._$Ei(),(this.l??=[]).push(s)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(s,e=qe){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(s)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(s,e),!e.noAccessor){let t=Symbol(),r=this.getPropertyDescriptor(s,t,e);r!==void 0&&vt(this.prototype,s,r)}}static getPropertyDescriptor(s,e,t){let{get:r,set:i}=yt(this.prototype,s)??{get(){return this[e]},set(n){this[e]=n}};return{get:r,set(n){let o=r?.call(this);i?.call(this,n),this.requestUpdate(s,o,t)},configurable:!0,enumerable:!0}}static getPropertyOptions(s){return this.elementProperties.get(s)??qe}static _$Ei(){if(this.hasOwnProperty(se("elementProperties")))return;let s=$t(this);s.finalize(),s.l!==void 0&&(this.l=[...s.l]),this.elementProperties=new Map(s.elementProperties)}static finalize(){if(this.hasOwnProperty(se("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(se("properties"))){let e=this.properties,t=[...xt(e),...wt(e)];for(let r of t)this.createProperty(r,e[r])}let s=this[Symbol.metadata];if(s!==null){let e=litPropertyMetadata.get(s);if(e!==void 0)for(let[t,r]of e)this.elementProperties.set(t,r)}this._$Eh=new Map;for(let[e,t]of this.elementProperties){let r=this._$Eu(e,t);r!==void 0&&this._$Eh.set(r,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(s){let e=[];if(Array.isArray(s)){let t=new Set(s.flat(1/0).reverse());for(let r of t)e.unshift(Ae(r))}else s!==void 0&&e.push(Ae(s));return e}static _$Eu(s,e){let t=e.attribute;return t===!1?void 0:typeof t=="string"?t:typeof s=="string"?s.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(s=>this.enableUpdating=s),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(s=>s(this))}addController(s){(this._$EO??=new Set).add(s),this.renderRoot!==void 0&&this.isConnected&&s.hostConnected?.()}removeController(s){this._$EO?.delete(s)}_$E_(){let s=new Map,e=this.constructor.elementProperties;for(let t of e.keys())this.hasOwnProperty(t)&&(s.set(t,this[t]),delete this[t]);s.size>0&&(this._$Ep=s)}createRenderRoot(){let s=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return Fe(s,this.constructor.elementStyles),s}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(s=>s.hostConnected?.())}enableUpdating(s){}disconnectedCallback(){this._$EO?.forEach(s=>s.hostDisconnected?.())}attributeChangedCallback(s,e,t){this._$AK(s,t)}_$ET(s,e){let t=this.constructor.elementProperties.get(s),r=this.constructor._$Eu(s,t);if(r!==void 0&&t.reflect===!0){let i=(t.converter?.toAttribute!==void 0?t.converter:ie).toAttribute(e,t.type);this._$Em=s,i==null?this.removeAttribute(r):this.setAttribute(r,i),this._$Em=null}}_$AK(s,e){let t=this.constructor,r=t._$Eh.get(s);if(r!==void 0&&this._$Em!==r){let i=t.getPropertyOptions(r),n=typeof i.converter=="function"?{fromAttribute:i.converter}:i.converter?.fromAttribute!==void 0?i.converter:ie;this._$Em=r;let o=n.fromAttribute(e,i.type);this[r]=o??this._$Ej?.get(r)??o,this._$Em=null}}requestUpdate(s,e,t,r=!1,i){if(s!==void 0){let n=this.constructor;if(r===!1&&(i=this[s]),t??=n.getPropertyOptions(s),!((t.hasChanged??_e)(i,e)||t.useDefault&&t.reflect&&i===this._$Ej?.get(s)&&!this.hasAttribute(n._$Eu(s,t))))return;this.C(s,e,t)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(s,e,{useDefault:t,reflect:r,wrapped:i},n){t&&!(this._$Ej??=new Map).has(s)&&(this._$Ej.set(s,n??e??this[s]),i!==!0||n!==void 0)||(this._$AL.has(s)||(this.hasUpdated||t||(e=void 0),this._$AL.set(s,e)),r===!0&&this._$Em!==s&&(this._$Eq??=new Set).add(s))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let s=this.scheduleUpdate();return s!=null&&await s,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[r,i]of this._$Ep)this[r]=i;this._$Ep=void 0}let t=this.constructor.elementProperties;if(t.size>0)for(let[r,i]of t){let{wrapped:n}=i,o=this[r];n!==!0||this._$AL.has(r)||o===void 0||this.C(r,void 0,i,o)}}let s=!1,e=this._$AL;try{s=this.shouldUpdate(e),s?(this.willUpdate(e),this._$EO?.forEach(t=>t.hostUpdate?.()),this.update(e)):this._$EM()}catch(t){throw s=!1,this._$EM(),t}s&&this._$AE(e)}willUpdate(s){}_$AE(s){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(s)),this.updated(s)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(s){return!0}update(s){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(s){}firstUpdated(s){}};H.elementStyles=[],H.shadowRootOptions={mode:"open"},H[se("elementProperties")]=new Map,H[se("finalized")]=new Map,St?.({ReactiveElement:H}),(me.reactiveElementVersions??=[]).push("2.1.2");var Ce=globalThis,Ke=a=>a,fe=Ce.trustedTypes,Ge=fe?fe.createPolicy("lit-html",{createHTML:a=>a}):void 0,et="$lit$",I=`lit$${Math.random().toFixed(9).slice(2)}$`,tt="?"+I,Nt=`<${tt}>`,V=document,ae=()=>V.createComment(""),oe=a=>a===null||typeof a!="object"&&typeof a!="function",He=Array.isArray,At=a=>He(a)||typeof a?.[Symbol.iterator]=="function",Ee=`[ 	
\f\r]`,ne=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,Ze=/-->/g,Je=/>/g,B=RegExp(`>|${Ee}(?:([^\\s"'>=/]+)(${Ee}*=${Ee}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),Xe=/'/g,Ye=/"/g,rt=/^(?:script|style|textarea|title)$/i,Pe=a=>(s,...e)=>({_$litType$:a,strings:s,values:e}),d=Pe(1),P=Pe(2),Gt=Pe(3),q=Symbol.for("lit-noChange"),h=Symbol.for("lit-nothing"),Qe=new WeakMap,F=V.createTreeWalker(V,129);function st(a,s){if(!He(a)||!a.hasOwnProperty("raw"))throw Error("invalid template strings array");return Ge!==void 0?Ge.createHTML(s):s}var Et=(a,s)=>{let e=a.length-1,t=[],r,i=s===2?"<svg>":s===3?"<math>":"",n=ne;for(let o=0;o<e;o++){let c=a[o],l,u,p=-1,g=0;for(;g<c.length&&(n.lastIndex=g,u=n.exec(c),u!==null);)g=n.lastIndex,n===ne?u[1]==="!--"?n=Ze:u[1]!==void 0?n=Je:u[2]!==void 0?(rt.test(u[2])&&(r=RegExp("</"+u[2],"g")),n=B):u[3]!==void 0&&(n=B):n===B?u[0]===">"?(n=r??ne,p=-1):u[1]===void 0?p=-2:(p=n.lastIndex-u[2].length,l=u[1],n=u[3]===void 0?B:u[3]==='"'?Ye:Xe):n===Ye||n===Xe?n=B:n===Ze||n===Je?n=ne:(n=B,r=void 0);let y=n===B&&a[o+1].startsWith("/>")?" ":"";i+=n===ne?c+Nt:p>=0?(t.push(l),c.slice(0,p)+et+c.slice(p)+I+y):c+I+(p===-2?o:y)}return[st(a,i+(a[e]||"<?>")+(s===2?"</svg>":s===3?"</math>":"")),t]},ce=class a{constructor({strings:s,_$litType$:e},t){let r;this.parts=[];let i=0,n=0,o=s.length-1,c=this.parts,[l,u]=Et(s,e);if(this.el=a.createElement(l,t),F.currentNode=this.el.content,e===2||e===3){let p=this.el.content.firstChild;p.replaceWith(...p.childNodes)}for(;(r=F.nextNode())!==null&&c.length<o;){if(r.nodeType===1){if(r.hasAttributes())for(let p of r.getAttributeNames())if(p.endsWith(et)){let g=u[n++],y=r.getAttribute(p).split(I),x=/([.?@])?(.*)/.exec(g);c.push({type:1,index:i,name:x[2],strings:y,ctor:x[1]==="."?ze:x[1]==="?"?Te:x[1]==="@"?Me:Y}),r.removeAttribute(p)}else p.startsWith(I)&&(c.push({type:6,index:i}),r.removeAttribute(p));if(rt.test(r.tagName)){let p=r.textContent.split(I),g=p.length-1;if(g>0){r.textContent=fe?fe.emptyScript:"";for(let y=0;y<g;y++)r.append(p[y],ae()),F.nextNode(),c.push({type:2,index:++i});r.append(p[g],ae())}}}else if(r.nodeType===8)if(r.data===tt)c.push({type:2,index:i});else{let p=-1;for(;(p=r.data.indexOf(I,p+1))!==-1;)c.push({type:7,index:i}),p+=I.length-1}i++}}static createElement(s,e){let t=V.createElement("template");return t.innerHTML=s,t}};function X(a,s,e=a,t){if(s===q)return s;let r=t!==void 0?e._$Co?.[t]:e._$Cl,i=oe(s)?void 0:s._$litDirective$;return r?.constructor!==i&&(r?._$AO?.(!1),i===void 0?r=void 0:(r=new i(a),r._$AT(a,e,t)),t!==void 0?(e._$Co??=[])[t]=r:e._$Cl=r),r!==void 0&&(s=X(a,r._$AS(a,s.values),r,t)),s}var Re=class{constructor(s,e){this._$AV=[],this._$AN=void 0,this._$AD=s,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(s){let{el:{content:e},parts:t}=this._$AD,r=(s?.creationScope??V).importNode(e,!0);F.currentNode=r;let i=F.nextNode(),n=0,o=0,c=t[0];for(;c!==void 0;){if(n===c.index){let l;c.type===2?l=new le(i,i.nextSibling,this,s):c.type===1?l=new c.ctor(i,c.name,c.strings,this,s):c.type===6&&(l=new We(i,this,s)),this._$AV.push(l),c=t[++o]}n!==c?.index&&(i=F.nextNode(),n++)}return F.currentNode=V,r}p(s){let e=0;for(let t of this._$AV)t!==void 0&&(t.strings!==void 0?(t._$AI(s,t,e),e+=t.strings.length-2):t._$AI(s[e])),e++}},le=class a{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(s,e,t,r){this.type=2,this._$AH=h,this._$AN=void 0,this._$AA=s,this._$AB=e,this._$AM=t,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let s=this._$AA.parentNode,e=this._$AM;return e!==void 0&&s?.nodeType===11&&(s=e.parentNode),s}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(s,e=this){s=X(this,s,e),oe(s)?s===h||s==null||s===""?(this._$AH!==h&&this._$AR(),this._$AH=h):s!==this._$AH&&s!==q&&this._(s):s._$litType$!==void 0?this.$(s):s.nodeType!==void 0?this.T(s):At(s)?this.k(s):this._(s)}O(s){return this._$AA.parentNode.insertBefore(s,this._$AB)}T(s){this._$AH!==s&&(this._$AR(),this._$AH=this.O(s))}_(s){this._$AH!==h&&oe(this._$AH)?this._$AA.nextSibling.data=s:this.T(V.createTextNode(s)),this._$AH=s}$(s){let{values:e,_$litType$:t}=s,r=typeof t=="number"?this._$AC(s):(t.el===void 0&&(t.el=ce.createElement(st(t.h,t.h[0]),this.options)),t);if(this._$AH?._$AD===r)this._$AH.p(e);else{let i=new Re(r,this),n=i.u(this.options);i.p(e),this.T(n),this._$AH=i}}_$AC(s){let e=Qe.get(s.strings);return e===void 0&&Qe.set(s.strings,e=new ce(s)),e}k(s){He(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,t,r=0;for(let i of s)r===e.length?e.push(t=new a(this.O(ae()),this.O(ae()),this,this.options)):t=e[r],t._$AI(i),r++;r<e.length&&(this._$AR(t&&t._$AB.nextSibling,r),e.length=r)}_$AR(s=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);s!==this._$AB;){let t=Ke(s).nextSibling;Ke(s).remove(),s=t}}setConnected(s){this._$AM===void 0&&(this._$Cv=s,this._$AP?.(s))}},Y=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(s,e,t,r,i){this.type=1,this._$AH=h,this._$AN=void 0,this.element=s,this.name=e,this._$AM=r,this.options=i,t.length>2||t[0]!==""||t[1]!==""?(this._$AH=Array(t.length-1).fill(new String),this.strings=t):this._$AH=h}_$AI(s,e=this,t,r){let i=this.strings,n=!1;if(i===void 0)s=X(this,s,e,0),n=!oe(s)||s!==this._$AH&&s!==q,n&&(this._$AH=s);else{let o=s,c,l;for(s=i[0],c=0;c<i.length-1;c++)l=X(this,o[t+c],e,c),l===q&&(l=this._$AH[c]),n||=!oe(l)||l!==this._$AH[c],l===h?s=h:s!==h&&(s+=(l??"")+i[c+1]),this._$AH[c]=l}n&&!r&&this.j(s)}j(s){s===h?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,s??"")}},ze=class extends Y{constructor(){super(...arguments),this.type=3}j(s){this.element[this.name]=s===h?void 0:s}},Te=class extends Y{constructor(){super(...arguments),this.type=4}j(s){this.element.toggleAttribute(this.name,!!s&&s!==h)}},Me=class extends Y{constructor(s,e,t,r,i){super(s,e,t,r,i),this.type=5}_$AI(s,e=this){if((s=X(this,s,e,0)??h)===q)return;let t=this._$AH,r=s===h&&t!==h||s.capture!==t.capture||s.once!==t.once||s.passive!==t.passive,i=s!==h&&(t===h||r);r&&this.element.removeEventListener(this.name,this,t),i&&this.element.addEventListener(this.name,this,s),this._$AH=s}handleEvent(s){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,s):this._$AH.handleEvent(s)}},We=class{constructor(s,e,t){this.element=s,this.type=6,this._$AN=void 0,this._$AM=e,this.options=t}get _$AU(){return this._$AM._$AU}_$AI(s){X(this,s)}};var Rt=Ce.litHtmlPolyfillSupport;Rt?.(ce,le),(Ce.litHtmlVersions??=[]).push("3.3.3");var it=(a,s,e)=>{let t=e?.renderBefore??s,r=t._$litPart$;if(r===void 0){let i=e?.renderBefore??null;t._$litPart$=r=new le(s.insertBefore(ae(),i),i,void 0,e??{})}return r._$AI(a),r};var je=globalThis,$=class extends H{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let s=super.createRenderRoot();return this.renderOptions.renderBefore??=s.firstChild,s}update(s){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(s),this._$Do=it(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return q}};$._$litElement$=!0,$.finalized=!0,je.litElementHydrateSupport?.({LitElement:$});var zt=je.litElementPolyfillSupport;zt?.({LitElement:$});(je.litElementVersions??=[]).push("4.2.2");var R=a=>(s,e)=>{e!==void 0?e.addInitializer(()=>{customElements.define(a,s)}):customElements.define(a,s)};var Tt={attribute:!0,type:String,converter:ie,reflect:!1,hasChanged:_e},Mt=(a=Tt,s,e)=>{let{kind:t,metadata:r}=e,i=globalThis.litPropertyMetadata.get(r);if(i===void 0&&globalThis.litPropertyMetadata.set(r,i=new Map),t==="setter"&&((a=Object.create(a)).wrapped=!0),i.set(e.name,a),t==="accessor"){let{name:n}=e;return{set(o){let c=s.get.call(this);s.set.call(this,o),this.requestUpdate(n,c,a,!0,o)},init(o){return o!==void 0&&this.C(n,void 0,a,o),o}}}if(t==="setter"){let{name:n}=e;return function(o){let c=this[n];s.call(this,o),this.requestUpdate(n,c,a,!0,o)}}throw Error("Unsupported decorator location: "+t)};function N(a){return(s,e)=>typeof e=="object"?Mt(a,s,e):((t,r,i)=>{let n=r.hasOwnProperty(i);return r.constructor.createProperty(i,t),n?Object.getOwnPropertyDescriptor(r,i):void 0})(a,s,e)}function k(a){return N({...a,state:!0,attribute:!1})}var T="goe_steve";function K(a){let s=new Map;for(let e of Object.values(a.entities))if(!(e.platform!==T||!e.device_id)&&!s.has(e.device_id)){let t=a.devices[e.device_id];s.set(e.device_id,t?.name_by_user||t?.name||e.device_id)}return[...s.entries()].map(([e,t])=>({id:e,name:t}))}function Q(a,s){let e={tag_energy:[]};if(!s){let i=K(a);i.length===1&&(s=i[0].id)}if(e.deviceId=s,!s)return e;let t=Object.values(a.entities).filter(i=>i.platform===T&&i.device_id===s),r=i=>{let n=t.find(c=>c.translation_key===i);return n?n.entity_id:t.find(c=>{let l=c.entity_id.split(".")[1]??"";return l===i||l.endsWith(`_${i}`)})?.entity_id};return e.status=r("status"),e.power_flow=r("power_flow"),e.surplus=r("surplus_for_car"),e.target_current=r("target_current"),e.controlling=r("controlling"),e.battery_hold=r("battery_hold"),e.charging_mode=r("charging_mode"),e.battery_hold_mode=r("battery_hold_mode"),e.smart_control=r("smart_control"),e.auto_phase=r("auto_phase"),e.manual_charge=r("manual_charge"),e.start_now=r("start_now"),e.manual_current=r("manual_current"),e.manual_phases=r("manual_phases"),e.battery_reserve_soc=r("battery_reserve_soc"),e.target_energy=r("target_energy"),e.departure=r("departure"),e.max_current=r("max_current"),e.min_current=r("min_current"),e.price_forecast=r("price_forecast"),e.cheap_price=r("cheap_price"),e.peak_window_power=r("peak_window_power"),e.monthly_peak=r("monthly_peak"),e.rolling_grid_power=r("rolling_grid_power"),e.peak_status=r("peak_status"),e.peak_guard_active=r("peak_guard_active"),e.peak_guard=r("peak_guard"),e.peak_follow_month=r("peak_follow_month"),e.grid_charge=r("grid_charge"),e.peak_soft_limit=r("peak_soft_limit"),e.peak_target_limit=r("peak_target_limit"),e.peak_hard_limit=r("peak_hard_limit"),e.peak_month_buffer=r("peak_month_buffer"),e.shaving_reserve_soc=r("shaving_reserve_soc"),e.peak_min_soc=r("peak_min_soc"),e.grid_setpoint=r("grid_setpoint"),e.cheap_charge_power=r("cheap_charge_power"),e.bright_day_target_soc=r("bright_day_target_soc"),e.dark_day_target_soc=r("dark_day_target_soc"),e.peak_ready_soc=r("peak_ready_soc"),e.stock_up=r("stock_up"),e.stock_up_target_soc=r("stock_up_target_soc"),e.reset_monthly_peak=r("reset_monthly_peak"),e.active_transaction=r("active_transaction"),e.last_session_energy=r("last_session_energy"),e.selected_tag=r("selected_tag"),e.tag_energy=t.filter(i=>i.translation_key==="tag_energy"||i.entity_id.split(".")[1]?.includes("_tag_energy_")).map(i=>i.entity_id).sort(),e}var Oe={"card.no_device":"No {name} device found. Set one up first, then add this card.","card.default_title":"Smart Charging","live.live":"live","live.updated_ago":"updated {ago} ago","hero.not_connected":"Not connected","hero.paused":"Paused","hero.paused_ready":"Paused \xB7 ready on {phases}-phase","hero.asked_takes":"asked {asked} A, car takes {takes} A","hero.solar_share":"{pct} % solar","hero.phase_count":"{phases}-phase","source.solar":"Solar","source.battery":"Battery","source.grid":"Grid","source.to_car":"{source} \u2192 car: {watts} of {total}","source.none":"Nothing flowing from {source} right now.","source.tap_hint":"Tap a segment for exact watts.","source.exporting":"House running on PV \u2014 surplus is exporting.","source.paused":"Car paused \u2014 no power flowing.","balance.pv":"PV","balance.house":"House","balance.grid":"Grid","balance.export":"Export","balance.battery":"Battery","balance.idle":"idle","balance.reserve":"reserve {pct}%","chip.hold":"Battery discharge blocked","chip.hold_manual":"Discharge blocked (manual)","chip.price_cheap":"{price} {unit} \u2014 cheap \u2713","chip.price_wait":"{price} {unit} \u2014 waiting for \u2264 {target}","chip.resume_in":"Can resume in {time}","chip.start_now":"Start now","chip.riding_out":"Riding out dip \xB7 {time}","chip.phases":"{phases} \u03C6","chip.forced_off":"Charger forced off","plan.on_track":"on track","plan.tight":"tight \u2014 few cheap hours","control.home_battery":"Home battery","control.smart_active":"Smart control is active","control.smart_inactive":"Smart control is off","control.mode":"Mode","mode_hint.manual":"You set current and phases \u2014 the charger holds them.","mode_hint.solar":"Charges only from solar surplus.","mode_hint.solar_min":"Uses solar surplus, topping up to a minimum rate from the home battery or the grid.","mode_hint.smart":"Targets the cheapest hours to reach your goal by departure.","mode_hint.fast":"Charges at full power right now.","control.manual_charge":"Charge now","control.manual_current":"Current","control.manual_phases":"Phases","control.smart_control":"Smart control","control.auto_phase":"Auto phase (1\u21943)","control.battery_reserve":"Keep battery above","control.target_energy":"Car target energy","control.departure":"Departure","control.max_current":"Max current","control.min_current":"Min current","control.tag":"Tag","live.target":"Target","live.surplus":"Surplus","action.start":"Start","action.stop":"Stop","action.start_charging":"Start charging","action.stop_charging":"Stop charging","action.stop_confirm":"Stop the active charging session?","session.none_hint":"No active session \u2014 plug in and pick a tag to start.","reason.smart_disabled":"Smart control disabled","reason.manual_passive":"Manual mode \u2014 charger left as-is","reason.manual_paused":"Manual mode \u2014 paused","reason.manual_charging":"Manual charging at {amps} A","reason.manual_charging_guarded":"Manual charging at {amps} A (protecting home battery)","reason.no_car":"No car connected","reason.awaiting_card":"Waiting for an RFID card \u2014 tap it at the wallbox to start","reason.car_not_drawing":"The car isn't taking power (full, or waiting on its own timer) \u2014 home battery released","reason.fast":"Fast charging at {amps} A","reason.cheap_grid":"Cheap grid {price}/kWh \u2264 {threshold} \u2192 full power","reason.cheap_grid_guarded":"Cheap grid {price}/kWh \u2264 {threshold} \u2192 full power (protecting home battery \u2192 {amps} A)","reason.deadline_plan":"Planned cheap hour at {price}/kWh \u2014 {remaining} kWh to go by departure","reason.deadline_plan_guarded":"Planned cheap hour at {price}/kWh \u2014 {remaining} kWh to go by departure (protecting home battery \u2192 {amps} A)","reason.deadline_urgent":"Charging now to make the departure target \u2014 {remaining} kWh to go","reason.deadline_urgent_peak":"Charging at full power to make the departure target \u2014 {remaining} kWh to go, so this quarter-hour will go over your peak limit","reason.target_reached":"Departure target reached \u2014 {delivered} kWh charged","reason.plan_waiting":"Waiting for a planned cheap hour","reason.waiting_battery_reserve":"Waiting \u2014 home battery {soc}% < reserve {reserve}%","reason.waiting_surplus":"Waiting for surplus \u2014 {surplus} W < {needed} W needed","reason.surplus_confirm":"Surplus {surplus} W \u2014 confirming before start","reason.surplus_ride_out":"Surplus dipped \u2014 riding it out at {amps} A","reason.solar_surplus":"Solar surplus {surplus} W \u2192 {amps} A","reason.solar_surplus_phase":"Solar surplus {surplus} W \u2192 {amps} A ({phases}-phase)","reason.solar_surplus_eased":"Solar surplus {surplus} W \u2192 {amps} A (easing off home battery)","reason.solar_surplus_battery_topup":"Solar surplus {surplus} W \u2192 {amps} A \u2014 the last {gap} W come from the home battery instead of being exported","reason.solar_min_covered":"Minimum {amps} A \u2014 the {surplus} W surplus covers it","reason.solar_min_topup":"Minimum {amps} A \u2014 surplus is only {surplus} W, so the last {gap} W come from the grid","reason.solar_min_topup_battery":"Minimum {amps} A \u2014 surplus is only {surplus} W, so the last {gap} W come from the home battery","session.none":"No active session","session.charging":"Charging: {state}","session.last":"Last session: {energy}","session.blocked":"blocked","session.tag":"tag","editor.device":"Smart Charging device (optional \u2014 auto-detected)","editor.title":"Title (optional)","editor.show_flow":"Show source bar & balance","editor.show_controls":"Show controls","editor.show_sessions":"Show sessions & RFID","editor.compact":"Compact (hide controls \u2014 wall dashboards)","editor.hours":"Hours to show (optional)","editor.charge_hours":"Cheapest-window length (0 hides it)","editor.demand_rate":"Demand charge per kW of monthly peak (optional)","editor.currency":"Currency symbol","editor.show_settings":"Show the settings block","chip.peak_soft":"Easing off \u2014 {projected} kW this \xBC h","chip.peak_hard":"Peak limit \u2014 {projected} kW this \xBC h","chip.peak_degraded":"Peak reading incomplete","chip.grid_charging":"Buying cheap \u2014 {power} W","peak.title":"Peak protection","peak.month_label":"Highest \xBC hour this month","peak.month_at":"on {when}","peak.month_none":"Nothing recorded yet this month","peak.month_cost":"\u2248 {cost} at {rate}/kW","peak.record_risk":"This quarter-hour is on track to beat it","peak.window_label":"This quarter-hour","peak.heading_for":"heading for {projected} kW","peak.time_left":"{time} left","peak.soft":"ease off","peak.target":"target","peak.hard":"hard","peak.allowance":"Limit raised to {value} kW \u2014 this month already cost {month} kW","peak.degraded":"Part of this quarter-hour went unmeasured \u2014 holding the limit","peak.off":"Measuring only. Turn on Peak protection to let it act.","peak.recent":"Recent quarter-hours","peak.recent_none":"No completed quarter-hours yet.","peak.forecast":"Cheap hours ahead","peak.forecast_none":"No price forecast available.","peak.buying_to":"Buying to {target} %","peak.bright":"bright tomorrow","peak.dark":"little sun tomorrow","peak.settings":"Settings","peak.limits":"Limits","peak.battery":"Home battery","peak.cheap":"Cheap hours","peak.stockUp":"Stocking up","reason.peak_off":"Peak protection is off","reason.peak_ok":"This quarter-hour is heading for {projected} kW \u2014 comfortable","reason.peak_watch":"This quarter-hour is heading for {projected} kW, close to the {soft} kW easing-off point","reason.peak_holding":"Holding this quarter-hour under {target} kW \u2014 at {projected} kW","reason.peak_shaving_car":"Heading for {projected} kW \u2014 easing the car back to {amps} A to stay under {target} kW","reason.peak_shaving_house":"Heading for {projected} kW \u2014 letting the home battery cover more of the house to stay under {target} kW","reason.peak_pause":"Heading for {projected} kW \u2014 the car is paused until this quarter-hour is over at {until}","reason.peak_battery_empty":"Heading for {projected} kW and the home battery is down to its {soc}% floor \u2014 nothing left to shave with","reason.peak_degraded":"The grid reading was missing for part of this quarter-hour \u2014 holding the current limit until {until} to be safe","reason.peak_month_headroom":"This month already peaked at {month} kW, so there is nothing to save by holding below it \u2014 aiming at {target} kW, just under the record","reason.grid_charge_dark":"Cheap hour at {price}/kWh and little sun expected \u2014 importing {power} W to fill the home battery to {target}%","reason.grid_charge_bright":"Cheap hour at {price}/kWh, but tomorrow looks bright \u2014 filling the home battery only to {target}% so the sun has somewhere to go","reason.grid_charge_full":"Home battery at {soc}% \u2014 nothing left to buy this cheaply","reason.grid_charge_ready":"Home battery down to {soc}% and too low to hold the peak limit \u2014 importing {power} W to get it back to {target}%, cheap hour or not","reason.grid_charge_stock_up":"Stocking up for tonight \u2014 importing {power} W to fill the home battery to {target}% and holding it there","reason.grid_charge_stocked":"Stocked up: home battery at {soc}%, holding it for tonight","price.title":"Electricity price","price.avg":"avg","price.no_price":"No price forecast available. Configure a price sensor for {name} first.","price.cheap_threshold":"Cheap below","price.cheap_hours":"{hours} cheap upcoming","price.next_window":"next {start}\u2013{end}","price.no_cheap":"No cheap hours coming up at this threshold","price.now":"now","price.tomorrow":"Tomorrow","price.cheapest_window":"Cheapest {hours} h"},Wt={"card.no_device":"Kein {name}-Ger\xE4t gefunden. Richte zuerst eines ein und f\xFCge dann diese Karte hinzu.","card.default_title":"Intelligentes Laden","live.live":"live","live.updated_ago":"vor {ago} aktualisiert","hero.not_connected":"Nicht verbunden","hero.paused":"Pausiert","hero.paused_ready":"Pausiert \xB7 bereit auf {phases}-phasig","hero.asked_takes":"angefordert {asked} A, Auto nimmt {takes} A","hero.solar_share":"{pct} % Solar","hero.phase_count":"{phases}-phasig","source.solar":"Solar","source.battery":"Batterie","source.grid":"Netz","source.to_car":"{source} \u2192 Auto: {watts} von {total}","source.none":"Aus {source} flie\xDFt gerade nichts.","source.tap_hint":"Segment antippen f\xFCr exakte Watt.","source.exporting":"Haus l\xE4uft auf PV \u2014 \xDCberschuss wird eingespeist.","source.paused":"Auto pausiert \u2014 kein Fluss.","balance.pv":"PV","balance.house":"Haus","balance.grid":"Netz","balance.export":"Einspeisung","balance.battery":"Batterie","balance.idle":"inaktiv","balance.reserve":"Reserve {pct}%","chip.hold":"Batterieentladung gesperrt","chip.hold_manual":"Entladung gesperrt (manuell)","chip.price_cheap":"{price} {unit} \u2014 g\xFCnstig \u2713","chip.price_wait":"{price} {unit} \u2014 warten auf \u2264 {target}","chip.resume_in":"Fortsetzen in {time}","chip.start_now":"Jetzt starten","chip.riding_out":"\xDCberbr\xFCcke Einbruch \xB7 {time}","chip.phases":"{phases} \u03C6","chip.forced_off":"Wallbox zwangsweise aus","plan.on_track":"im Plan","plan.tight":"knapp \u2014 wenige g\xFCnstige Stunden","control.home_battery":"Hausbatterie","control.smart_active":"Intelligente Steuerung aktiv","control.smart_inactive":"Intelligente Steuerung aus","control.mode":"Modus","mode_hint.manual":"Du gibst Strom und Phasen vor \u2014 die Wallbox h\xE4lt sie.","mode_hint.solar":"L\xE4dt nur aus Solar\xFCberschuss.","mode_hint.solar_min":"Nutzt Solar\xFCberschuss und stockt bis zu einer Mindestrate aus Hausbatterie oder Netz auf.","mode_hint.smart":"Steuert die g\xFCnstigsten Stunden an, um dein Ziel bis zur Abfahrt zu erreichen.","mode_hint.fast":"L\xE4dt jetzt mit voller Leistung.","control.manual_charge":"Jetzt laden","control.manual_current":"Stromst\xE4rke","control.manual_phases":"Phasen","control.smart_control":"Intelligente Steuerung","control.auto_phase":"Auto-Phase (1\u21943)","control.battery_reserve":"Batterie halten \xFCber","control.target_energy":"Ziel-Energie Auto","control.departure":"Abfahrt","control.max_current":"Max. Strom","control.min_current":"Min. Strom","control.tag":"Tag","live.target":"Ziel","live.surplus":"\xDCberschuss","action.start":"Starten","action.stop":"Stoppen","action.start_charging":"Laden starten","action.stop_charging":"Laden stoppen","action.stop_confirm":"Aktiven Ladevorgang stoppen?","session.none_hint":"Kein aktiver Ladevorgang \u2014 einstecken und einen Tag w\xE4hlen.","reason.smart_disabled":"Intelligente Steuerung deaktiviert","reason.manual_passive":"Manueller Modus \u2014 Wallbox unver\xE4ndert","reason.manual_paused":"Manueller Modus \u2014 pausiert","reason.manual_charging":"Manuelles Laden mit {amps} A","reason.manual_charging_guarded":"Manuelles Laden mit {amps} A (Hausbatterie gesch\xFCtzt)","reason.no_car":"Kein Auto verbunden","reason.awaiting_card":"Warte auf eine RFID-Karte \u2014 an der Wallbox hinhalten zum Starten","reason.car_not_drawing":"Das Auto nimmt keine Leistung auf (voll oder eigener Ladetimer) \u2014 Hausbatterie freigegeben","reason.fast":"Schnellladen mit {amps} A","reason.cheap_grid":"G\xFCnstiger Netzstrom {price}/kWh \u2264 {threshold} \u2192 volle Leistung","reason.cheap_grid_guarded":"G\xFCnstiger Netzstrom {price}/kWh \u2264 {threshold} \u2192 volle Leistung (Hausbatterie gesch\xFCtzt \u2192 {amps} A)","reason.deadline_plan":"Geplante G\xFCnstig-Stunde zu {price}/kWh \u2014 noch {remaining} kWh bis zur Abfahrt","reason.deadline_plan_guarded":"Geplante G\xFCnstig-Stunde zu {price}/kWh \u2014 noch {remaining} kWh bis zur Abfahrt (Hausbatterie gesch\xFCtzt \u2192 {amps} A)","reason.deadline_urgent":"L\xE4dt jetzt, um das Abfahrtsziel zu erreichen \u2014 noch {remaining} kWh","reason.deadline_urgent_peak":"L\xE4dt mit voller Leistung f\xFCr das Abfahrtsziel \u2014 noch {remaining} kWh, daher \xFCberschreitet diese Viertelstunde die Lastspitzen-Grenze","reason.target_reached":"Abfahrtsziel erreicht \u2014 {delivered} kWh geladen","reason.plan_waiting":"Warten auf eine geplante G\xFCnstig-Stunde","reason.waiting_battery_reserve":"Warten \u2014 Hausbatterie {soc}% < Reserve {reserve}%","reason.waiting_surplus":"Warten auf \xDCberschuss \u2014 {surplus} W < {needed} W ben\xF6tigt","reason.surplus_confirm":"\xDCberschuss {surplus} W \u2014 kurze Best\xE4tigung vor dem Start","reason.surplus_ride_out":"\xDCberschuss eingebrochen \u2014 \xFCberbr\xFCckt mit {amps} A","reason.solar_surplus":"Solar\xFCberschuss {surplus} W \u2192 {amps} A","reason.solar_surplus_phase":"Solar\xFCberschuss {surplus} W \u2192 {amps} A ({phases}-phasig)","reason.solar_surplus_eased":"Solar\xFCberschuss {surplus} W \u2192 {amps} A (Hausbatterie wird entlastet)","reason.solar_surplus_battery_topup":"Solar\xFCberschuss {surplus} W \u2192 {amps} A \u2014 die letzten {gap} W kommen aus der Hausbatterie statt ins Netz zu gehen","reason.solar_min_covered":"Minimum {amps} A \u2014 {surplus} W \xDCberschuss decken das","reason.solar_min_topup":"Minimum {amps} A \u2014 nur {surplus} W \xDCberschuss, die letzten {gap} W kommen aus dem Netz","reason.solar_min_topup_battery":"Minimum {amps} A \u2014 nur {surplus} W \xDCberschuss, die letzten {gap} W kommen aus der Hausbatterie","session.none":"Kein aktiver Ladevorgang","session.charging":"L\xE4dt: {state}","session.last":"Letzter Ladevorgang: {energy}","session.blocked":"gesperrt","session.tag":"Tag","editor.device":"Smart-Charging-Ger\xE4t (optional \u2014 automatisch erkannt)","editor.title":"Titel (optional)","editor.show_flow":"Quellenbalken & Bilanz anzeigen","editor.show_controls":"Steuerung anzeigen","editor.show_sessions":"Ladevorg\xE4nge & RFID anzeigen","editor.compact":"Kompakt (Steuerung ausblenden \u2014 Wand-Dashboards)","editor.hours":"Anzuzeigende Stunden (optional)","editor.charge_hours":"L\xE4nge des G\xFCnstig-Fensters (0 blendet es aus)","editor.demand_rate":"Leistungspreis je kW Monatsspitze (optional)","editor.currency":"W\xE4hrungssymbol","editor.show_settings":"Einstellungen anzeigen","chip.peak_soft":"Nimmt zur\xFCck \u2014 {projected} kW diese \xBC h","chip.peak_hard":"Lastspitze \u2014 {projected} kW diese \xBC h","chip.peak_degraded":"Messung der Spitze unvollst\xE4ndig","chip.grid_charging":"Kauft g\xFCnstig \u2014 {power} W","peak.title":"Lastspitzenschutz","peak.month_label":"H\xF6chste \xBC Stunde dieses Monats","peak.month_at":"am {when}","peak.month_none":"Diesen Monat noch nichts erfasst","peak.month_cost":"\u2248 {cost} bei {rate}/kW","peak.record_risk":"Diese Viertelstunde ist auf dem Weg, das zu \xFCbertreffen","peak.window_label":"Diese Viertelstunde","peak.heading_for":"l\xE4uft auf {projected} kW zu","peak.time_left":"noch {time}","peak.soft":"zur\xFCcknehmen","peak.target":"Ziel","peak.hard":"hart","peak.allowance":"Grenze auf {value} kW angehoben \u2014 der Monat kostet bereits {month} kW","peak.degraded":"Ein Teil dieser Viertelstunde wurde nicht gemessen \u2014 Grenze bleibt","peak.off":"Nur Messung. Schalte den Lastspitzenschutz ein, damit er eingreift.","peak.recent":"Letzte Viertelstunden","peak.recent_none":"Noch keine abgeschlossene Viertelstunde.","peak.forecast":"G\xFCnstige Stunden voraus","peak.forecast_none":"Keine Preisprognose verf\xFCgbar.","peak.buying_to":"Kauft bis {target} %","peak.bright":"morgen sonnig","peak.dark":"morgen wenig Sonne","peak.settings":"Einstellungen","peak.limits":"Grenzen","peak.battery":"Hausbatterie","peak.cheap":"G\xFCnstige Stunden","peak.stockUp":"Vorladen","reason.peak_off":"Lastspitzenschutz ist aus","reason.peak_ok":"Diese Viertelstunde l\xE4uft auf {projected} kW zu \u2014 entspannt","reason.peak_watch":"Diese Viertelstunde l\xE4uft auf {projected} kW zu, nahe an der Zur\xFCcknehmen-Schwelle von {soft} kW","reason.peak_holding":"H\xE4lt diese Viertelstunde unter {target} kW \u2014 aktuell {projected} kW","reason.peak_shaving_car":"L\xE4uft auf {projected} kW zu \u2014 nimmt das Auto auf {amps} A zur\xFCck, um unter {target} kW zu bleiben","reason.peak_shaving_house":"L\xE4uft auf {projected} kW zu \u2014 die Hausbatterie \xFCbernimmt mehr vom Haus, um unter {target} kW zu bleiben","reason.peak_pause":"L\xE4uft auf {projected} kW zu \u2014 das Auto pausiert, bis diese Viertelstunde um {until} vorbei ist","reason.peak_battery_empty":"L\xE4uft auf {projected} kW zu und die Hausbatterie ist auf ihrer {soc}%-Grenze \u2014 nichts mehr zum Kappen da","reason.peak_degraded":"Der Netzwert fehlte f\xFCr einen Teil dieser Viertelstunde \u2014 die Grenze bleibt bis {until} bestehen","reason.peak_month_headroom":"Dieser Monat hatte bereits {month} kW Spitze \u2014 darunter zu bleiben spart nichts mehr; Ziel sind {target} kW, knapp darunter","reason.grid_charge_dark":"G\xFCnstige Stunde zu {price}/kWh und wenig Sonne erwartet \u2014 bezieht {power} W, um die Hausbatterie auf {target}% zu f\xFCllen","reason.grid_charge_bright":"G\xFCnstige Stunde zu {price}/kWh, aber morgen wird es sonnig \u2014 f\xFCllt die Hausbatterie nur auf {target}%, damit die Sonne noch Platz hat","reason.grid_charge_full":"Hausbatterie bei {soc}% \u2014 zu diesem Preis gibt es nichts mehr zu kaufen","reason.grid_charge_ready":"Hausbatterie nur noch bei {soc}% und zu leer, um die Lastspitze zu halten \u2014 bezieht {power} W zur\xFCck auf {target}%, g\xFCnstige Stunde hin oder her","reason.grid_charge_stock_up":"L\xE4dt f\xFCr heute Abend vor \u2014 bezieht {power} W, um die Hausbatterie auf {target}% zu f\xFCllen und dort zu halten","reason.grid_charge_stocked":"Vorgeladen: Hausbatterie bei {soc}%, wird f\xFCr heute Abend gehalten","price.title":"Strompreis","price.avg":"Mittel","price.no_price":"Keine Preisprognose verf\xFCgbar. Richte zuerst einen Preissensor f\xFCr {name} ein.","price.cheap_threshold":"G\xFCnstig unter","price.cheap_hours":"{hours} g\xFCnstig in K\xFCrze","price.next_window":"n\xE4chste {start}\u2013{end}","price.no_cheap":"Bei dieser Schwelle keine g\xFCnstigen Stunden in Sicht","price.now":"jetzt","price.tomorrow":"Morgen","price.cheapest_window":"G\xFCnstigste {hours} h"},Ct={en:Oe,de:Wt};function Ht(a){let s=(a?.locale?.language||a?.language||"en").toLowerCase().split("-")[0];return Ct[s]??Oe}function v(a,s,e={}){let r=Ht(a)[s]??Oe[s]??s;for(let[i,n]of Object.entries(e))r=r.replace(`{${i}}`,n);return r}var G=class extends ${constructor(){super(...arguments);this._schema=[{name:"device",selector:{device:{integration:T}}},{name:"title",selector:{text:{}}},{type:"grid",name:"",schema:[{name:"show_flow",selector:{boolean:{}}},{name:"show_controls",selector:{boolean:{}}},{name:"show_sessions",selector:{boolean:{}}},{name:"compact",selector:{boolean:{}}}]}];this._label=e=>{switch(e.name){case"device":return v(this.hass,"editor.device");case"title":return v(this.hass,"editor.title");case"show_flow":return v(this.hass,"editor.show_flow");case"show_controls":return v(this.hass,"editor.show_controls");case"show_sessions":return v(this.hass,"editor.show_sessions");case"compact":return v(this.hass,"editor.compact");default:return e.name}}}setConfig(e){this._config=e}render(){return!this.hass||!this._config?h:d`<ha-form
      .hass=${this.hass}
      .data=${this._config}
      .schema=${this._schema}
      .computeLabel=${this._label}
      @value-changed=${this._valueChanged}
    ></ha-form>`}_valueChanged(e){let t={...e.detail.value};this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:t},bubbles:!0,composed:!0}))}};G.styles=S`
    ha-form {
      display: block;
      padding: 8px 0;
    }
  `,_([N({attribute:!1})],G.prototype,"hass",2),_([k()],G.prototype,"_config",2),G=_([R("goe-steve-card-editor")],G);var Z=class extends ${constructor(){super(...arguments);this._schema=[{name:"device",selector:{device:{integration:T}}},{name:"title",selector:{text:{}}},{name:"hours",selector:{number:{min:6,max:48,mode:"box",unit_of_measurement:"h"}}},{name:"charge_hours",selector:{number:{min:0,max:12,step:.5,mode:"box",unit_of_measurement:"h"}}}];this._label=e=>{switch(e.name){case"device":return v(this.hass,"editor.device");case"title":return v(this.hass,"editor.title");case"hours":return v(this.hass,"editor.hours");case"charge_hours":return v(this.hass,"editor.charge_hours");default:return e.name}}}setConfig(e){this._config=e}render(){return!this.hass||!this._config?h:d`<ha-form
      .hass=${this.hass}
      .data=${this._config}
      .schema=${this._schema}
      .computeLabel=${this._label}
      @value-changed=${this._valueChanged}
    ></ha-form>`}_valueChanged(e){let t={...e.detail.value};this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:t},bubbles:!0,composed:!0}))}};Z.styles=S`
    ha-form {
      display: block;
      padding: 8px 0;
    }
  `,_([N({attribute:!1})],Z.prototype,"hass",2),_([k()],Z.prototype,"_config",2),Z=_([R("goe-steve-price-card-editor")],Z);var Pt="go-e + SteVe Smart Charging",C=480,ye=200,m={left:38,right:10,top:12,bottom:24},nt=C-m.left-m.right,ve=ye-m.top-m.bottom,ee=36e5,j=class extends ${constructor(){super(...arguments);this._dragValue=null;this._hoverIndex=null;this._dragging=!1;this._cheapCache=null}get _chargeHours(){let e=this._config?.charge_hours;return e===void 0?3:e}static getConfigElement(){return document.createElement("goe-steve-price-card-editor")}static getStubConfig(e){return{type:"custom:goe-steve-price-card",device:K(e)[0]?.id}}setConfig(e){this._config={...e}}getCardSize(){return 6}get _entities(){return this.hass?Q(this.hass,this._config?.device):null}_t(e,t={}){return v(this.hass,e,t)}_stateObj(e){return e?this.hass.states[e]:void 0}_deviceName(e){if(!e)return null;let t=this.hass.devices[e];return t?.name_by_user||t?.name||null}_slots(e){let r=(e.attributes.slots??[]).map(i=>({start:Date.parse(i.start??""),price:Number(i.price)})).filter(i=>!Number.isNaN(i.start)&&!Number.isNaN(i.price)).sort((i,n)=>i.start-n.start);return r.map((i,n)=>({start:i.start,end:n+1<r.length?r[n+1].start:i.start+ee,price:i.price}))}_cheap(e,t){let r=this._stateObj(e.cheap_price),i=Number(t.attributes.cheap_price),n=r?Number(r.state):Number.isNaN(i)?.15:i,o=r?.attributes??{};return{obj:r,value:n,min:Number(o.min??0),max:Number(o.max??1),step:Number(o.step??.01),unit:t.attributes.unit??o.unit_of_measurement??""}}render(){if(!this.hass||!this._config)return h;let e=this._entities,t=this._stateObj(e?.price_forecast),r=t?this._slots(t):[],i=this._deviceName(e?.deviceId),n=this._config.title??(i?`${i} \xB7 ${this._t("price.title")}`:this._t("price.title"));if(!t||r.length===0){let[l,u]=this._t("price.no_price").split("{name}");return d`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:cash-clock"></ha-icon>
          <p>${l}<b>${Pt}</b>${u??""}</p>
        </div>
      </ha-card>`}let o=this._cheap(e,t),c=this._dragValue??o.value;return d`<ha-card>
      <div class="header">
        <div class="title-row">
          <ha-icon icon="mdi:cash-clock"></ha-icon>
          <span class="title">${n}</span>
        </div>
        <div class="now-price">${this._fmtPrice(Number(t.state),o.unit)}</div>
      </div>
      ${this._renderStats(r,o.unit)}
      ${this._renderChart(r,c)}
      ${this._renderPreview(r,c)}
      ${this._renderThresholdInput(o,c)}
    </ha-card>`}_shownSlots(e){let t=Date.now(),r=e.filter(i=>i.end>t);if(r.length===0&&(r=e.slice(-1)),this._config.hours&&this._config.hours>0){let i=t+this._config.hours*ee;r=r.filter(n=>n.start<i)}return r.slice(0,96)}_renderChart(e,t){let r=Date.now(),i=this._shownSlots(e),n=i[0].start,o=i[i.length-1].end,c=i.map(b=>b.price),l=Math.min(...c),u=Math.max(...c),p=Math.min(l,t),g=Math.max(u,t),y=g-p||1,x=p-y*.1,z=g+y*.1,A=b=>m.left+(b-n)/(o-n)*nt,f=b=>m.top+(1-(b-x)/(z-x))*ve,M=m.top+ve,W=f(t),lt=this._weightedMean(i),ke=f(lt),dt=i.map((b,E)=>{let D=A(b.start),pt=A(b.end),Ie=f(b.price),ut=b.price<=t,gt=r>=b.start&&r<b.end,mt=E===this._hoverIndex;return P`<rect
        class="bar ${gt?"now-bar":""} ${mt?"hover-bar":""}"
        fill=${this._barFill(b.price,ut,t,u)}
        x=${D+.5}
        y=${Ie}
        width=${Math.max(.5,pt-D-1)}
        height=${Math.max(0,M-Ie)}
      ></rect>`}),te=this._chargeHours>0?this._bestWindow(i,this._chargeHours):null,ht=te&&te.endIdx>te.startIdx-1?(()=>{let b=A(te.start),E=A(te.end);return P`<g class="best-window">
              <rect x=${b} y=${m.top} width=${Math.max(0,E-b)} height=${ve}></rect>
              <line x1=${b} y1=${m.top} x2=${b} y2=${M}></line>
              <line x1=${E} y1=${m.top} x2=${E} y2=${M}></line>
              <text x=${(b+E)/2} y=${m.top+21}>${this._t("price.cheapest_window",{hours:this._fmtHours(this._chargeHours)})}</text>
            </g>`})():h,Se=[];for(let b of i){let E=new Date(b.start);if(E.getHours()===0&&E.getMinutes()===0&&b.start>n){let D=A(b.start);Se.push(P`<line class="day-div" x1=${D} y1=${m.top} x2=${D} y2=${M}></line>`),Se.push(P`<text class="day-lbl" x=${D+3} y=${m.top+9}>${this._t("price.tomorrow")}</text>`)}}let De=[];for(let b of i){let E=new Date(b.start);if(E.getHours()%6===0&&E.getMinutes()===0){let D=A(b.start);De.push(P`<text class="x-tick" x=${D} y=${ye-8}>${String(E.getHours()).padStart(2,"0")}</text>`)}}let pe=r>=n&&r<=o?A(r):null;return d`<div class="chart">
      <svg
        viewBox="0 0 ${C} ${ye}"
        preserveAspectRatio="none"
        @pointermove=${this._onPointerMove}
        @pointerdown=${this._onChartPointerDown}
        @pointerup=${this._onPointerUp}
        @pointercancel=${this._onPointerUp}
        @pointerleave=${this._onPointerLeave}
      >
        <!-- y grid: min / avg / threshold / max -->
        <text class="y-tick" x=${m.left-4} y=${f(z)+3}>${this._fmtNum(g)}</text>
        <text class="y-tick" x=${m.left-4} y=${M}>${this._fmtNum(p)}</text>
        <text class="y-tick thresh-tick" x=${m.left-4} y=${W+3}>${this._fmtNum(t)}</text>
        ${ht}
        ${Se}
        ${dt}
        ${De}
        <!-- average reference line -->
        <line class="avg-line" x1=${m.left} y1=${ke} x2=${C-m.right} y2=${ke}></line>
        <text class="avg-lbl" x=${m.left+2} y=${ke-2}>Ø</text>
        ${pe!==null?P`<line class="now-line" x1=${pe} y1=${m.top} x2=${pe} y2=${M}></line>
                 <text class="now-tick" x=${pe} y=${m.top-2}>${this._t("price.now")}</text>`:h}
        <!-- threshold line + draggable handle -->
        <line class="thresh" x1=${m.left} y1=${W} x2=${C-m.right} y2=${W}></line>
        <g class="handle" data-handle @pointerdown=${this._onPointerDown}>
          <!-- generous, invisible touch target so fingers can grab the handle -->
          <rect class="handle-hit" x=${C-m.right-68} y=${W-20} width="72" height="40"></rect>
          <rect class="handle-chip" x=${C-m.right-52} y=${W-9} width="52" height="18" rx="4"></rect>
          <text x=${C-m.right-26} y=${W+4}>${this._fmtNum(t)}</text>
        </g>
      </svg>
      ${this._renderTooltip(i,A,f)}
    </div>`}_barFill(e,t,r,i){if(e<0||t)return"var(--success-color, #2e7d32)";let n=i-r||1,o=Math.max(0,Math.min(1,(e-r)/n)),c=45-o*37,l=55-o*8;return`hsl(${c.toFixed(0)}, 85%, ${l.toFixed(0)}%)`}_weightedMean(e){let t=0,r=0;for(let i of e){let n=(i.end-i.start)/ee;t+=n,r+=i.price*n}return t>0?r/t:0}_bestWindow(e,t){let r=null;for(let i=0;i<e.length;i++){let n=0,o=0,c=i;for(;c<e.length&&n<t-1e-9;){let u=(e[c].end-e[c].start)/ee;n+=u,o+=e[c].price*u,c++}if(n<t-1e-9)break;let l=o/n;(!r||l<r.mean)&&(r={start:e[i].start,end:e[c-1].end,mean:l,startIdx:i,endIdx:c-1})}return r}_renderTooltip(e,t,r){let i=this._hoverIndex;if(i===null||i<0||i>=e.length)return h;let n=e[i],c=(t(n.start)+t(n.end))/2/C*100,l=Math.max(2,r(n.price)-4),u=this._entities&&this._stateObj(this._entities.price_forecast)?.attributes.unit;return d`<div
      class="tip"
      style="left: calc(8px + ${c.toFixed(2)}% - ${(c/100*16).toFixed(2)}px); top: ${l}px;"
    >
      <span class="tip-time">${this._fmtTime(n.start)}–${this._fmtTime(n.end)}</span>
      <span class="tip-price">${this._fmtNum(n.price)}${u?` ${u}`:""}</span>
    </div>`}_slotAtClientX(e){let t=this._entities,r=this._stateObj(t?.price_forecast),i=r?this._slots(r):[],n=this._shownSlots(i);if(n.length===0)return null;let o=this.renderRoot.querySelector("svg");if(!o)return null;let c=o.getBoundingClientRect(),l=n[0].start,u=n[n.length-1].end,g=(e-c.left)/c.width*C;if(g<m.left||g>C-m.right)return null;let y=l+(g-m.left)/nt*(u-l),x=n.findIndex(z=>y>=z.start&&y<z.end);return x>=0?x:null}_onChartPointerDown(e){this._dragging||(this._hoverIndex=this._slotAtClientX(e.clientX))}_onPointerLeave(){this._hoverIndex!==null&&(this._hoverIndex=null)}_onPointerDown(e){let t=this._entities,r=this._stateObj(t?.price_forecast);!t||!r||!t.cheap_price||(this._cheapCache=this._cheap(t,r),this._dragging=!0,this._hoverIndex=null,e.target.setPointerCapture?.(e.pointerId),e.preventDefault(),this._updateDrag(e))}_onPointerMove(e){if(!this._dragging){let t=this._slotAtClientX(e.clientX);t!==this._hoverIndex&&(this._hoverIndex=t);return}this._hoverIndex=null,e.preventDefault(),this._updateDrag(e)}_onPointerUp(){if(!this._dragging)return;this._dragging=!1;let e=this._cheapCache,t=this._dragValue;this._dragValue=null,this._cheapCache=null,e?.obj&&t!==null&&t!==e.value&&this.hass.callService("number","set_value",{entity_id:e.obj.entity_id,value:t})}_updateDrag(e){let t=this._cheapCache;if(!t)return;let r=this.renderRoot.querySelector("svg");if(!r)return;let i=r.getBoundingClientRect(),n=(e.clientY-i.top)/i.height*ye,{yMin:o,yMax:c}=this._yDomain(t),l=1-(n-m.top)/ve,u=o+l*(c-o);u=Math.min(t.max,Math.max(t.min,u)),t.step>0&&(u=Math.round(u/t.step)*t.step);let p=(String(t.step).split(".")[1]??"").length||2;this._dragValue=Number(u.toFixed(p))}_yDomain(e){let t=this._entities,r=this._stateObj(t?.price_forecast),i=r?this._slots(r):[],n=this._shownSlots(i),o=this._dragValue??e.value,c=n.map(g=>g.price),l=Math.min(...c,o),u=Math.max(...c,o),p=u-l||1;return{yMin:l-p*.1,yMax:u+p*.1}}_renderPreview(e,t){let r=Date.now(),n=e.filter(p=>p.end>r).filter(p=>p.price<=t);if(n.length===0)return d`<div class="preview muted">
        <ha-icon icon="mdi:flash-off"></ha-icon><span>${this._t("price.no_cheap")}</span>
      </div>`;let o=n.reduce((p,g)=>p+(Math.min(g.end,r+48*ee)-Math.max(g.start,r))/ee,0),c=n[0],l=c.end;for(let p=1;p<n.length&&n[p].start===l;p++)l=n[p].end;let u=`${o.toFixed(o<10?1:0)} h`;return d`<div class="preview">
      <ha-icon icon="mdi:flash"></ha-icon>
      <span>${this._t("price.cheap_hours",{hours:u})}</span>
      <span class="sep">·</span>
      <span class="muted"
        >${this._t("price.next_window",{start:this._fmtTime(Math.max(c.start,r)),end:this._fmtTime(l)})}</span
      >
    </div>`}_renderStats(e,t){let r=this._shownSlots(e);if(r.length===0)return h;let i=r.map(u=>u.price),n=Math.min(...i),o=Math.max(...i),c=this._weightedMean(r),l=t?` ${t}`:"";return d`<div class="stats">
      <span class="stat"><span class="stat-k stat-min">▼</span>${this._fmtNum(n)}${l}</span>
      <span class="stat"><span class="stat-k">${this._t("price.avg")}</span>${this._fmtNum(c)}${l}</span>
      <span class="stat"><span class="stat-k stat-max">▲</span>${this._fmtNum(o)}${l}</span>
    </div>`}_renderThresholdInput(e,t){return e.obj?d`<div class="threshold-row">
      <span class="thr-label">${this._t("price.cheap_threshold")}</span>
      <span class="thr-input">
        <input
          type="number"
          .value=${String(t)}
          min=${e.min}
          max=${e.max}
          step=${e.step}
          @change=${r=>this._setThreshold(e,r.target.value)}
        />
        ${e.unit?d`<span class="thr-unit">${e.unit}</span>`:h}
      </span>
    </div>`:h}_setThreshold(e,t){let r=Number(t);!e.obj||Number.isNaN(r)||r===e.value||this.hass.callService("number","set_value",{entity_id:e.obj.entity_id,value:r})}_fmtNum(e){return e.toFixed(Math.abs(e)<1?2:1)}_fmtPrice(e,t){return Number.isNaN(e)?"\u2014":`${this._fmtNum(e)}${t?` ${t}`:""}`}_fmtHours(e){return Number.isInteger(e)?String(e):e.toFixed(1)}_fmtTime(e){return new Date(e).toLocaleTimeString(this.hass?.locale?.language??[],{hour:"2-digit",minute:"2-digit"})}};j.styles=S`
    ha-card {
      overflow: hidden;
      padding-bottom: 8px;
    }
    .empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      padding: 24px;
      color: var(--secondary-text-color);
      text-align: center;
    }
    .empty ha-icon {
      --mdc-icon-size: 40px;
      color: var(--disabled-text-color);
    }
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 16px 16px 8px;
    }
    .title-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .title-row ha-icon {
      color: var(--primary-color);
    }
    .title {
      font-size: 1.25rem;
      font-weight: 500;
    }
    .now-price {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--primary-text-color);
    }

    /* Stat row */
    .stats {
      display: flex;
      gap: 16px;
      padding: 0 16px 4px;
      font-size: 0.85rem;
      color: var(--secondary-text-color);
    }
    .stat {
      display: inline-flex;
      align-items: baseline;
      gap: 4px;
    }
    .stat-k {
      font-size: 0.75rem;
      opacity: 0.9;
    }
    .stat-min {
      color: var(--success-color, #2e7d32);
    }
    .stat-max {
      color: hsl(8, 85%, 47%);
    }

    /* Chart */
    .chart {
      padding: 0 8px;
      position: relative;
    }
    .chart svg {
      width: 100%;
      height: 200px;
      /* default touch-action: vertical swipes scroll the page normally;
         only the handle (below) owns the drag gesture. */
    }
    /* Bar fill is set inline per-bar (heat gradient / accent / negative),
       so no base fill here — a CSS fill would override the attribute. */
    .now-bar {
      stroke: var(--primary-text-color);
      stroke-width: 1;
    }
    .hover-bar {
      filter: brightness(1.12);
    }

    /* Cheapest-window highlight — green, matching the "cheap" bars */
    .best-window rect {
      fill: var(--success-color, #2e7d32);
      opacity: 0.12;
      pointer-events: none;
    }
    .best-window line {
      stroke: var(--success-color, #2e7d32);
      stroke-width: 1;
      stroke-dasharray: 3 2;
      opacity: 0.7;
      pointer-events: none;
    }
    .best-window text {
      fill: var(--success-color, #2e7d32);
      font-size: 9px;
      font-weight: 600;
      text-anchor: middle;
      pointer-events: none;
    }

    /* Average reference line */
    .avg-line {
      stroke: var(--secondary-text-color);
      stroke-width: 1;
      stroke-dasharray: 1 3;
      opacity: 0.6;
    }
    .avg-lbl {
      fill: var(--secondary-text-color);
      font-size: 9px;
    }

    /* Hover tooltip */
    .tip {
      position: absolute;
      transform: translate(-50%, -100%);
      pointer-events: none;
      background: var(--primary-text-color);
      color: var(--card-background-color, var(--ha-card-background, #fff));
      border-radius: 6px;
      padding: 3px 7px;
      font-size: 0.72rem;
      line-height: 1.35;
      white-space: nowrap;
      display: flex;
      flex-direction: column;
      align-items: center;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
      z-index: 2;
    }
    .tip-price {
      font-weight: 600;
    }
    .thresh {
      stroke: var(--primary-color);
      stroke-width: 1.5;
      stroke-dasharray: 4 3;
    }
    .handle {
      /* the handle is the only element that owns the touch gesture, so a
         scroll swipe elsewhere on the chart pans the page as usual. */
      touch-action: none;
    }
    .handle rect {
      cursor: ns-resize;
      touch-action: none;
    }
    .handle-chip {
      fill: var(--primary-color);
    }
    .handle-hit {
      fill: transparent;
    }
    .handle text {
      fill: var(--text-primary-color, #fff);
      font-size: 11px;
      font-weight: 600;
      text-anchor: middle;
    }
    .now-line {
      stroke: var(--primary-text-color);
      stroke-width: 1.5;
    }
    .now-tick {
      fill: var(--primary-text-color);
      font-size: 9px;
      font-weight: 600;
      text-anchor: middle;
    }
    .day-div {
      stroke: var(--divider-color);
      stroke-width: 1;
      stroke-dasharray: 2 3;
    }
    .day-lbl {
      fill: var(--secondary-text-color);
      font-size: 9px;
    }
    .x-tick {
      fill: var(--secondary-text-color);
      font-size: 9px;
      text-anchor: middle;
    }
    .y-tick {
      fill: var(--secondary-text-color);
      font-size: 9px;
      text-anchor: end;
    }
    .thresh-tick {
      fill: var(--primary-color);
      font-weight: 600;
    }

    /* Preview */
    .preview {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 16px 2px;
      font-size: 0.9rem;
      color: var(--primary-text-color);
    }
    .preview ha-icon {
      --mdc-icon-size: 18px;
      color: var(--primary-color);
    }
    .preview.muted,
    .preview .muted {
      color: var(--secondary-text-color);
    }
    .preview.muted ha-icon {
      color: var(--secondary-text-color);
    }
    .preview .sep {
      color: var(--secondary-text-color);
    }

    /* Threshold numeric input */
    .threshold-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 8px 16px 4px;
    }
    .thr-label {
      color: var(--secondary-text-color);
      font-size: 0.9rem;
    }
    .thr-input {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .thr-input input {
      width: 90px;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--ha-card-background));
      color: var(--primary-text-color);
      font-family: inherit;
      font-size: 0.95rem;
      text-align: right;
    }
    .thr-input input:focus {
      outline: none;
      border-color: var(--primary-color);
    }
    .thr-unit {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
    }
  `,_([N({attribute:!1})],j.prototype,"hass",2),_([k()],j.prototype,"_config",2),_([k()],j.prototype,"_dragValue",2),_([k()],j.prototype,"_hoverIndex",2),j=_([R("goe-steve-price-card")],j);window.customCards=window.customCards||[];window.customCards.push({type:"goe-steve-price-card",name:"go-e + SteVe Price",description:"Electricity-price forecast with a draggable 'cheap' threshold \u2014 see the curve and set what counts as cheap.",preview:!0,documentationURL:"https://github.com/JustChr/HAgoe_steve"});var Le=a=>a??h;var J=class extends ${constructor(){super(...arguments);this._schema=[{name:"device",selector:{device:{integration:T}}},{name:"title",selector:{text:{}}},{name:"demand_rate",selector:{number:{min:0,max:500,step:.01,mode:"box"}}},{name:"currency",selector:{text:{}}},{name:"show_settings",selector:{boolean:{}}}];this._label=e=>{switch(e.name){case"device":return v(this.hass,"editor.device");case"title":return v(this.hass,"editor.title");case"demand_rate":return v(this.hass,"editor.demand_rate");case"currency":return v(this.hass,"editor.currency");case"show_settings":return v(this.hass,"editor.show_settings");default:return e.name}}}setConfig(e){this._config=e}render(){return!this.hass||!this._config?h:d`<ha-form
      .hass=${this.hass}
      .data=${this._config}
      .schema=${this._schema}
      .computeLabel=${this._label}
      @value-changed=${this._valueChanged}
    ></ha-form>`}_valueChanged(e){let t={...e.detail.value};this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:t},bubbles:!0,composed:!0}))}};J.styles=S`
    ha-form {
      display: block;
      padding: 8px 0;
    }
  `,_([N({attribute:!1})],J.prototype,"hass",2),_([k()],J.prototype,"_config",2),J=_([R("goe-steve-peak-card-editor")],J);function de(a){if(!a||["unknown","unavailable",""].includes(a.state))return null;let s=Number(a.state);if(Number.isNaN(s))return null;let e=(n,o)=>{let c=Number(a.attributes[n]);return Number.isNaN(c)?o:c},t=e("soft_w",3300),r=e("target_w",3700),i=e("hard_w",3900);return{averageW:s,projectedW:e("projected_w",s),softW:t,targetW:r,hardW:i,effectiveSoftW:e("effective_soft_w",t),effectiveTargetW:e("effective_target_w",r),effectiveHardW:e("effective_hard_w",i),degraded:a.attributes.degraded===!0,tier:String(a.attributes.tier??"off")}}function jt(a,s){return a>=s.effectiveHardW?"hard":a>=s.effectiveSoftW?"soft":"ok"}function xe(a,s){let e=Math.max(a.effectiveHardW*1.25,a.projectedW*1.05,1),t=c=>Math.max(0,Math.min(100,c/e*100)),r=t(a.averageW),i=Math.max(0,t(a.projectedW)-r),n=jt(a.projectedW,a),o=(c,l,u)=>c<=0||c>=e?h:d`<span class="pb-tick ${l}" style="left:${t(c)}%" title="${u}"></span>`;return d`<div class="pb">
    <div class="pb-track ${a.degraded?"degraded":""}">
      <span class="pb-fill ${n}" style="width:${r}%"></span>
      <span class="pb-ghost ${n}" style="left:${r}%;width:${i}%"></span>
      ${o(a.effectiveSoftW,"soft",s.left)}
      ${o(a.effectiveTargetW,"target","")}
      ${o(a.effectiveHardW,"hard","")}
    </div>
    <div class="pb-labels">
      <span>${s.left}</span>
      <span class="pb-right">${s.right}</span>
    </div>
  </div>`}var we=S`
  .pb {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .pb-track {
    position: relative;
    height: 10px;
    border-radius: 999px;
    background: var(--divider-color);
    overflow: hidden;
  }
  .pb-track.degraded {
    /* Hatched: the number is a floor we can stand behind, not a measurement. */
    background-image: repeating-linear-gradient(
      45deg,
      transparent 0 4px,
      var(--card-background-color) 4px 8px
    );
  }
  .pb-fill,
  .pb-ghost {
    position: absolute;
    top: 0;
    bottom: 0;
  }
  .pb-fill {
    left: 0;
    border-radius: 999px 0 0 999px;
  }
  .pb-fill.ok {
    background: var(--goe-battery);
  }
  .pb-fill.soft {
    background: var(--warning-color, #c05252);
  }
  .pb-fill.hard {
    background: var(--error-color, #db4437);
  }
  .pb-ghost {
    opacity: 0.35;
  }
  .pb-ghost.ok {
    background: var(--goe-battery);
  }
  .pb-ghost.soft {
    background: var(--warning-color, #c05252);
  }
  .pb-ghost.hard {
    background: var(--error-color, #db4437);
  }
  .pb-tick {
    position: absolute;
    top: -2px;
    bottom: -2px;
    width: 2px;
    background: var(--primary-text-color);
    opacity: 0.45;
  }
  .pb-tick.hard {
    opacity: 0.75;
  }
  .pb-labels {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    font-size: 0.72rem;
    color: var(--secondary-text-color);
    font-variant-numeric: tabular-nums;
  }
  .pb-right {
    text-align: right;
  }
`;var Ot="go-e + SteVe Smart Charging",at=36e5,O=a=>{let s=Number(a);return Number.isNaN(s)?NaN:s},ot=a=>{let s=O(a);return Number.isNaN(s)?void 0:String(s)},Lt=a=>{let s=Math.max(0,Math.round(a));return`${Math.floor(s/60)}:${String(s%60).padStart(2,"0")}`},U=class extends ${constructor(){super(...arguments);this._now=Date.now()}static getConfigElement(){return document.createElement("goe-steve-peak-card-editor")}static getStubConfig(e){return{type:"custom:goe-steve-peak-card",device:K(e)[0]?.id}}setConfig(e){this._config={show_settings:!0,...e}}getCardSize(){return 6}connectedCallback(){super.connectedCallback(),this._timer=window.setInterval(()=>{this._now=Date.now()},1e3)}disconnectedCallback(){super.disconnectedCallback(),this._timer&&window.clearInterval(this._timer)}get _entities(){if(this.hass)return Q(this.hass,this._config?.device)}_t(e,t={}){return v(this.hass,e,t)}_stateObj(e){return e?this.hass.states[e]:void 0}_deviceName(e){let t=this.hass.devices?.[e];return t?.name_by_user||t?.name}render(){if(!this.hass||!this._config)return h;let e=this._entities;if(!e||!e.deviceId||!e.peak_window_power)return d`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:transmission-tower-off"></ha-icon>
          <p>${this._renderNoDevice()}</p>
        </div>
      </ha-card>`;let t=this._config.title??this._deviceName(e.deviceId)??this._t("peak.title");return d`<ha-card>
      <div class="hacard">
        ${this._renderHead(t)} ${this._renderMonth(e)} ${this._renderWindow(e)}
        ${this._renderWhy(e)} ${this._renderRecent(e)} ${this._renderBuying(e)}
        ${this._config.show_settings?this._renderSettings(e):h}
      </div>
    </ha-card>`}_renderNoDevice(){let[e,t]=this._t("card.no_device").split("{name}");return d`${e}<b>${Ot}</b>${t??""}`}_renderHead(e){return d`<div class="c-head">
      <ha-icon icon="mdi:transmission-tower-off"></ha-icon>
      <span class="title">${e}</span>
    </div>`}_renderMonth(e){let t=this._stateObj(e.monthly_peak),r=O(t?.state),i=t?.attributes?.record_at_risk===!0,n=t?.attributes?.peak_at,o=Number.isNaN(r)||r<=0?this._t("peak.month_none"):`${(r/1e3).toFixed(2)} kW`,c=this._config.demand_rate,l=c&&!Number.isNaN(r)&&r>0?this._t("peak.month_cost",{cost:`${(r/1e3*c).toFixed(2)} ${this._config.currency??""}`.trim(),rate:`${c} ${this._config.currency??""}`.trim()}):"";return d`<div class="month">
      <div class="month-label">${this._t("peak.month_label")}</div>
      <div class="month-value ${i?"risk":""}">${o}</div>
      <div class="month-sub">
        ${n?this._t("peak.month_at",{when:this._fmtDate(n)}):""}
        ${l?d`<span class="cost">${l}</span>`:h}
      </div>
      ${i?d`<div class="risk-note">
            <ha-icon icon="mdi:alert"></ha-icon>${this._t("peak.record_risk")}
          </div>`:h}
    </div>`}_renderWindow(e){let t=this._stateObj(e.peak_window_power),r=de(t);if(!r)return h;let i=this._countdown(t?.attributes?.window_ends),n=i===null?"":this._t("peak.time_left",{time:Lt(i)}),o=this._t("peak.heading_for",{projected:(r.projectedW/1e3).toFixed(2)}),c=O(t?.attributes?.month_peak_w),l=r.effectiveTargetW>r.targetW+1?d`<div class="note">
            ${this._t("peak.allowance",{value:(r.effectiveTargetW/1e3).toFixed(2),month:((Number.isNaN(c)?r.effectiveHardW:c)/1e3).toFixed(2)})}
          </div>`:h;return d`<div class="window">
      <div class="section-label">${this._t("peak.window_label")}</div>
      ${xe(r,{left:o,right:n})}
      <div class="scale">
        <span>${this._t("peak.soft")} ${(r.effectiveSoftW/1e3).toFixed(1)}</span>
        <span>${this._t("peak.target")} ${(r.effectiveTargetW/1e3).toFixed(1)}</span>
        <span>${this._t("peak.hard")} ${(r.effectiveHardW/1e3).toFixed(1)}</span>
      </div>
      ${l}
      ${r.degraded?d`<div class="note warn">${this._t("peak.degraded")}</div>`:h}
      ${t?.attributes?.enabled===!1?d`<div class="note">${this._t("peak.off")}</div>`:h}
    </div>`}_renderWhy(e){let t=this._stateObj(e.peak_status);if(!t)return h;let r=t.attributes?.reason_key,n=t.state&&t.state!=="unknown"?t.state:"\u2014";if(r){let o=t.attributes?.reason_params??{},c=this._t(`reason.${r}`,o);c!==`reason.${r}`&&(n=c)}return d`<div class="why">${n}</div>`}_renderRecent(e){let t=this._stateObj(e.peak_window_power),r=t?.attributes?.history??[],i=de(t);if(!r.length||!i)return d`<div class="recent">
        <div class="section-label">${this._t("peak.recent")}</div>
        <div class="note">${this._t("peak.recent_none")}</div>
      </div>`;let n=r.slice(-8),o=Math.max(i.effectiveHardW*1.25,...n.map(([,l])=>l),1),c=O(this._stateObj(e.monthly_peak)?.state);return d`<div class="recent">
      <div class="section-label">${this._t("peak.recent")}</div>
      <div class="bars">
        ${n.map(([l,u])=>{let p=u>=i.effectiveHardW?"hard":u>=i.effectiveSoftW?"soft":"ok",g=!Number.isNaN(c)&&u>=c&&c>0;return d`<div class="bar-col" title="${(u/1e3).toFixed(2)} kW">
            <div class="bar-slot">
              <div
                class="bar ${p} ${g?"record":""}"
                style="height:${Math.max(2,u/o*100)}%"
              ></div>
            </div>
            <span class="bar-time">${this._fmtTime(l)}</span>
          </div>`})}
      </div>
    </div>`}_renderBuying(e){let t=this._stateObj(e.price_forecast),r=this._stateObj(e.peak_status);if(!t)return h;let i=t.attributes?.slots??[],n=O(t.attributes?.cheap_price??this._stateObj(e.cheap_price)?.state),o=i.map(f=>({start:Date.parse(f.start),price:Number(f.price)})).filter(f=>!Number.isNaN(f.start)&&f.start+at>this._now).slice(0,24);if(!o.length||Number.isNaN(n))return d`<div class="buying">
        <div class="section-label">${this._t("peak.forecast")}</div>
        <div class="note">${this._t("peak.forecast_none")}</div>
      </div>`;let c=Math.max(...o.map(f=>f.price),n),l=Math.min(...o.map(f=>f.price),0),u=c-l||1,p=e.bright_day_target_soc?O(this._stateObj(e.bright_day_target_soc)?.state):NaN,g=e.dark_day_target_soc?O(this._stateObj(e.dark_day_target_soc)?.state):NaN,y=r?.attributes?.reason_params??{},x=O(y.target),z=!Number.isNaN(x)&&x===p&&p!==g,A=Number.isNaN(x)?g:x;return d`<div class="buying">
      <div class="section-label">${this._t("peak.forecast")}</div>
      <div class="pricebars">
        ${o.map(f=>{let M=f.price<=n,W=f.start<=this._now&&f.start+at>this._now;return d`<div
            class="pricebar ${M?"cheap":""} ${W?"now":""}"
            style="height:${Math.max(3,(f.price-l)/u*100)}%"
            title="${new Date(f.start).getHours()}:00 — ${f.price}"
          ></div>`})}
      </div>
      ${Number.isNaN(A)?h:d`<div class="note">
            ${this._t("peak.buying_to",{target:String(Math.round(A))})} ·
            ${this._t(z?"peak.bright":"peak.dark")}
          </div>`}
    </div>`}_renderSettings(e){let t=i=>i?d`<div class="setting">
            <span class="setting-name">${this._friendlyName(i)}</span>
            <ha-entity-toggle
              .hass=${this.hass}
              .stateObj=${this._stateObj(i)}
            ></ha-entity-toggle>
          </div>`:h,r=i=>{let n=i?this._stateObj(i):void 0;if(!i||!n)return h;let o=n.attributes??{},c=o.unit_of_measurement,l=n.state==="unavailable"||n.state==="unknown";return d`<div class="setting">
        <span class="setting-name">${this._friendlyName(i)}</span>
        <span class="numfield">
          <input
            type="number"
            inputmode="decimal"
            .value=${l?"":n.state}
            step=${O(o.step)||1}
            min=${Le(ot(o.min))}
            max=${Le(ot(o.max))}
            ?disabled=${l}
            aria-label=${this._friendlyName(i)}
            @change=${u=>this._setNumber(i,u)}
          />
          ${c?d`<span class="unit">${c}</span>`:h}
        </span>
      </div>`};return d`<div class="settings">
      <div class="section-label">${this._t("peak.settings")}</div>
      ${t(e.peak_guard)} ${t(e.peak_follow_month)} ${t(e.grid_charge)}
      <div class="group-label">${this._t("peak.limits")}</div>
      ${r(e.peak_soft_limit)} ${r(e.peak_target_limit)}
      ${r(e.peak_hard_limit)} ${r(e.peak_month_buffer)}
      <div class="group-label">${this._t("peak.battery")}</div>
      ${r(e.shaving_reserve_soc)} ${r(e.peak_min_soc)}
      ${r(e.peak_ready_soc)}
      <div class="group-label">${this._t("peak.cheap")}</div>
      ${r(e.grid_setpoint)} ${r(e.cheap_charge_power)}
      ${r(e.bright_day_target_soc)} ${r(e.dark_day_target_soc)}
      ${e.stock_up||e.stock_up_target_soc?d`<div class="group-label">${this._t("peak.stockUp")}</div>
            ${t(e.stock_up)} ${r(e.stock_up_target_soc)}`:h}
      ${e.reset_monthly_peak?d`<div class="setting">
            <span class="setting-name">${this._friendlyName(e.reset_monthly_peak)}</span>
            <ha-icon-button
              .path=${"M12,5V1L7,6L12,11V7A6,6 0 0,1 18,13A6,6 0 0,1 12,19A6,6 0 0,1 6,13H4A8,8 0 0,0 12,21A8,8 0 0,0 20,13A8,8 0 0,0 12,5Z"}
              @click=${()=>this._press(e.reset_monthly_peak)}
            ></ha-icon-button>
          </div>`:h}
    </div>`}_friendlyName(e){let t=this._stateObj(e)?.attributes?.friendly_name??e,r=this._entities?.deviceId?this._deviceName(this._entities.deviceId):void 0;return r&&t.startsWith(`${r} `)?t.slice(r.length+1):t}_setNumber(e,t){let r=Number(t.target.value);Number.isNaN(r)||this.hass.callService("number","set_value",{entity_id:e,value:r})}_press(e){this.hass.callService("button","press",{entity_id:e})}_countdown(e){if(typeof e!="string")return null;let t=Date.parse(e);if(Number.isNaN(t))return null;let r=(t-this._now)/1e3;return r>0?r:null}_lang(){return this.hass?.locale?.language??this.hass?.language??"en"}_fmtTime(e){let t=Date.parse(e);return Number.isNaN(t)?"":new Intl.DateTimeFormat(this._lang(),{hour:"2-digit",minute:"2-digit"}).format(new Date(t))}_fmtDate(e){let t=Date.parse(e);return Number.isNaN(t)?"":new Intl.DateTimeFormat(this._lang(),{day:"numeric",month:"short",hour:"2-digit",minute:"2-digit"}).format(new Date(t))}};U.styles=[we,S`
      :host {
        --goe-battery: var(--success-color, #3f9e68);
        --goe-accent: var(--primary-color);
      }
      ha-card {
        overflow: hidden;
      }
      .hacard {
        display: flex;
        flex-direction: column;
        gap: 14px;
        padding: 14px 16px 16px;
      }
      .empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 8px;
        padding: 24px 16px;
        text-align: center;
        color: var(--secondary-text-color);
      }
      .empty ha-icon {
        --mdc-icon-size: 32px;
      }
      .c-head {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .c-head ha-icon {
        --mdc-icon-size: 20px;
        color: var(--goe-accent);
      }
      .title {
        font-weight: 600;
      }
      .section-label,
      .group-label {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--secondary-text-color);
      }
      .group-label {
        margin-top: 6px;
      }
      .month {
        display: flex;
        flex-direction: column;
        gap: 2px;
      }
      .month-label {
        font-size: 0.76rem;
        color: var(--secondary-text-color);
      }
      .month-value {
        font-size: 2.1rem;
        font-weight: 600;
        line-height: 1.1;
        font-variant-numeric: tabular-nums;
      }
      .month-value.risk {
        color: var(--error-color, #db4437);
      }
      .month-sub {
        display: flex;
        gap: 10px;
        font-size: 0.78rem;
        color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums;
      }
      .risk-note {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 4px;
        font-size: 0.78rem;
        color: var(--error-color, #db4437);
      }
      .risk-note ha-icon {
        --mdc-icon-size: 16px;
      }
      .window,
      .recent,
      .buying,
      .settings {
        display: flex;
        flex-direction: column;
        gap: 6px;
      }
      .scale {
        display: flex;
        justify-content: space-between;
        font-size: 0.7rem;
        color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums;
      }
      .why {
        font-size: 0.85rem;
        color: var(--primary-text-color);
      }
      .note {
        font-size: 0.74rem;
        color: var(--secondary-text-color);
      }
      .note.warn {
        color: var(--warning-color, #c05252);
      }
      .bars,
      .pricebars {
        display: flex;
        align-items: flex-end;
        gap: 3px;
        height: 64px;
      }
      .bar-col {
        display: flex;
        flex: 1;
        flex-direction: column;
        align-items: center;
        gap: 3px;
        height: 100%;
      }
      .bar-slot {
        display: flex;
        align-items: flex-end;
        width: 100%;
        flex: 1;
      }
      .bar {
        width: 100%;
        border-radius: 3px 3px 0 0;
        background: var(--goe-battery);
      }
      .bar.soft {
        background: var(--warning-color, #c05252);
      }
      .bar.hard {
        background: var(--error-color, #db4437);
      }
      .bar.record {
        outline: 1px solid var(--primary-text-color);
        outline-offset: 1px;
      }
      .bar-time {
        font-size: 0.62rem;
        color: var(--secondary-text-color);
        font-variant-numeric: tabular-nums;
      }
      .pricebar {
        flex: 1;
        border-radius: 2px 2px 0 0;
        background: var(--divider-color);
      }
      .pricebar.cheap {
        background: var(--goe-battery);
      }
      .pricebar.now {
        outline: 1px solid var(--goe-accent);
        outline-offset: 1px;
      }
      .settings {
        border-top: 1px solid var(--divider-color);
        padding-top: 10px;
      }
      .setting {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        min-height: 32px;
      }
      .setting-name {
        font-size: 0.82rem;
      }
      .numfield {
        display: flex;
        align-items: center;
        gap: 4px;
        flex: 0 0 auto;
        padding: 2px 8px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        background: var(--card-background-color, transparent);
      }
      .numfield:focus-within {
        border-color: var(--goe-accent);
      }
      .numfield input {
        width: 62px;
        border: none;
        padding: 4px 0;
        background: none;
        color: var(--primary-text-color);
        font: inherit;
        font-size: 0.86rem;
        text-align: right;
        font-variant-numeric: tabular-nums;
      }
      .numfield input:focus {
        outline: none;
      }
      .numfield input:disabled {
        color: var(--disabled-text-color, var(--secondary-text-color));
      }
      /* The spinners steal width and misfire on touch; the keyboard still steps. */
      .numfield input::-webkit-outer-spin-button,
      .numfield input::-webkit-inner-spin-button {
        margin: 0;
        -webkit-appearance: none;
      }
      .numfield input[type="number"] {
        -moz-appearance: textfield;
        appearance: textfield;
      }
      .unit {
        font-size: 0.76rem;
        color: var(--secondary-text-color);
      }
      :focus-visible {
        outline: 2px solid var(--goe-accent);
        outline-offset: 2px;
      }
    `],_([N({attribute:!1})],U.prototype,"hass",2),_([k()],U.prototype,"_config",2),_([k()],U.prototype,"_now",2),U=_([R("goe-steve-peak-card")],U);window.customCards=window.customCards||[];window.customCards.push({type:"goe-steve-peak-card",name:"go-e + SteVe Peak protection",description:"This month's billed peak, the live billing quarter-hour against its limits, what set the peak, and the settings behind it.",preview:!0,documentationURL:"https://github.com/JustChr/HAgoe_steve"});var Dt="go-e + SteVe Smart Charging",It=45,Ut=230,ct=a=>{if(a==null||Number.isNaN(a))return"\u2014";let s=Math.abs(a);return s>=1e3?`${(a/1e3).toFixed(s>=1e4?0:1)} kW`:`${Math.round(a)} W`},he=a=>a==null||Number.isNaN(a)?"\u2014":`${(a/1e3).toFixed(1)} kW`,$e=a=>{let s=Math.max(0,Math.round(a)),e=Math.floor(s/3600),t=Math.floor(s%3600/60),r=s%60;return(e?`${e}:${String(t).padStart(2,"0")}`:`${t}`)+`:${String(r).padStart(2,"0")}`},w=a=>{let s=Number(a);return Number.isNaN(s)?NaN:s},L=class extends ${constructor(){super(...arguments);this._now=Date.now();this._optimistic=new Map;this._splitNote=null}static getConfigElement(){return document.createElement("goe-steve-card-editor")}static getStubConfig(e){return{type:"custom:goe-steve-card",device:K(e)[0]?.id}}setConfig(e){this._config={show_flow:!0,show_controls:!0,show_sessions:!0,compact:!1,...e}}getCardSize(){return 8}connectedCallback(){super.connectedCallback(),this._timer=window.setInterval(()=>{this._now=Date.now()},1e3)}disconnectedCallback(){super.disconnectedCallback(),this._timer&&window.clearInterval(this._timer)}get _entities(){return this.hass?Q(this.hass,this._config?.device):null}_t(e,t={}){return v(this.hass,e,t)}render(){if(!this.hass||!this._config)return h;let e=this._entities;if(!e||!e.deviceId)return d`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:ev-station"></ha-icon>
          <p>${this._renderNoDevice()}</p>
        </div>
      </ha-card>`;let t=this._config.title??this._deviceName(e.deviceId)??this._t("card.default_title"),r=this._config.show_controls&&!this._config.compact;return d`<ha-card>
      <div class="hacard">
        ${this._renderHead(e,t)}
        ${this._renderHero(e)}
        ${this._renderWhy(e)}
        ${this._config.show_flow?this._renderSplit(e):h}
        ${this._renderPeak(e)}
        ${this._renderChips(e)}
        ${this._renderPlan(e)}
        ${r?this._renderControls(e):h}
        ${this._config.show_sessions?this._renderSession(e):h}
      </div>
    </ha-card>`}_renderPeak(e){let t=this._stateObj(e.peak_window_power);if(!t||t.attributes?.enabled!==!0)return h;let r=de(t);if(!r)return h;let i=this._t("peak.heading_for",{projected:this._fmtKwNum(r.projectedW)}),n=this._countdown(t.attributes?.window_ends),o=n===null?this._t("peak.window_label"):this._t("peak.time_left",{time:$e(n)});return d`<div class="peakstrip">${xe(r,{left:i,right:o})}</div>`}_renderNoDevice(){let[e,t]=this._t("card.no_device").split("{name}");return d`${e}<b>${Dt}</b>${t??""}`}_renderHead(e,t){let r=this._stateObj(e.status),i=this._isOn(e.controlling),n=this._ageSeconds(r??this._stateObj(e.power_flow)),o=n!==null&&n>It,c=o?this._t("live.updated_ago",{ago:this._fmtAgo(n)}):this._t("live.live"),l=i?this._t("control.smart_active"):this._t("control.smart_inactive");return d`<div class="c-head">
      <ha-icon
        class="brain ${i?"":"off"}"
        icon="mdi:brain"
        title=${l}
        aria-label=${l}
      ></ha-icon>
      <span class="c-title">${t}</span>
      <span class="livedot ${o?"stale":""}"><i></i>${c}</span>
    </div>`}_renderHero(e){let t=this._stateObj(e.power_flow)?.attributes??{},r=this._stateObj(e.status)?.attributes??{},i=w(t.car_w),n=r.charging===!0||i>50,o=t.car_connected,c=w(t.phases),l=this._sourceShares(t),u=2*Math.PI*44,p=0,g=(f,M)=>{let W=P`<circle
        cx="50" cy="50" r="44" stroke="${M}"
        style="stroke-dasharray:${Math.max(f,0)*u} ${u};
               stroke-dashoffset:${-p*u};
               opacity:${f>0?1:0}"></circle>`;return p+=Math.max(f,0),W},y=l.total>0?Math.round(l.solar/l.total*100):0,x=w(r.target_current_a),z=n&&c>0?i/(c*Ut):NaN,A=this._heroSub(o,n,c,x,z);return d`<div class="c-hero">
      <div class="ringwrap">
        <div class="ring ${n?"on":""}">
          <svg viewBox="0 0 100 100" fill="none" stroke-width="7" stroke-linecap="round">
            <circle class="track" cx="50" cy="50" r="44"></circle>
            ${g(l.total?l.grid/l.total:0,"var(--goe-grid)")}
            ${g(l.total?l.battery/l.total:0,"var(--goe-battery)")}
            ${g(l.total?l.solar/l.total:0,"var(--goe-solar)")}
          </svg>
          <div class="caric">
            <ha-icon icon="${o===!1?"mdi:car-off":"mdi:car-electric"}"></ha-icon>
          </div>
        </div>
        ${n&&l.total>0?d`<div class="solarbadge">
              <ha-icon icon="mdi:solar-power"></ha-icon>${this._t("hero.solar_share",{pct:String(y)})}
            </div>`:h}
      </div>
      <div class="heroright">
        <div class="power">
          ${Number.isNaN(i)?"\u2014":(i/1e3).toFixed(1)} <small>kW</small>
        </div>
        <div class="herosub">${A}</div>
      </div>
    </div>`}_heroSub(e,t,r,i,n){if(e===!1)return this._t("hero.not_connected");if(!t)return r>0?this._t("hero.paused_ready",{phases:String(r)}):this._t("hero.paused");let o=[];return!Number.isNaN(n)&&!Number.isNaN(i)&&Math.abs(i-n)>=1.5?o.push(this._t("hero.asked_takes",{asked:String(Math.round(i)),takes:String(Math.round(n))})):!Number.isNaN(i)&&i>0?o.push(`${Math.round(i)} A`):Number.isNaN(n)||o.push(`${Math.round(n)} A`),r>0&&o.push(this._t("hero.phase_count",{phases:String(r)})),o.join(" \xB7 ")}_renderWhy(e){let t=this._stateObj(e.status);return d`<div class="why">${this._statusReason(t)}</div>`}_renderSplit(e){let t=this._stateObj(e.power_flow)?.attributes??{},r=this._stateObj(e.status)?.attributes??{},i=w(t.car_w),n=r.charging===!0||i>50,o=this._sourceShares(t),c=l=>{let u=o.total>0?o[l]/o.total:0;if(u<=.001)return h;let p=this._t(`source.${l}`);return d`<button
        class="seg-src ${l}"
        style="flex-grow:${Math.max(u*100,.001)}"
        @click=${()=>this._tapSource(l,o[l],i)}
      >
        ${u>.14?`${p} ${Math.round(u*100)} %`:u>.05?`${Math.round(u*100)} %`:""}
      </button>`};return d`<div class="split">
      <div class="splitbar ${n?"flowing":""}">
        ${c("solar")}${c("battery")}${c("grid")}
      </div>
      <div class="splitnote" id="splitnote">
        ${this._splitNote??this._defaultSplitNote(o.total,t)}
      </div>
      ${this._renderBalance(e,t)}
    </div>`}_tapSource(e,t,r){let i=this._t(`source.${e}`);this._splitNote=t>0?this._t("source.to_car",{source:i,watts:ct(t),total:he(r)}):this._t("source.none",{source:i}),this.requestUpdate()}_defaultSplitNote(e,t){return e>0?this._t("source.tap_hint"):t.car_connected===!1?this._t("source.exporting"):this._t("source.paused")}_renderBalance(e,t){let r=w(t.pv_w),i=w(t.house_w),n=w(t.grid_w),o=t.battery_w===null||t.battery_w===void 0?null:w(t.battery_w),c=t.battery_soc,l=w(this._stateObj(e.battery_reserve_soc)?.state),u=this._holdActive(e),p=[];if(Number.isNaN(r)||p.push(d`<span><i class="dot" style="background:var(--goe-solar)"></i>${this._t("balance.pv")} <b>${he(r)}</b></span>`),Number.isNaN(i)||p.push(d`<span>${this._t("balance.house")} <b>${he(i)}</b></span>`),Number.isNaN(n)||p.push(d`<span><i class="dot" style="background:var(--goe-grid)"></i>${n<-50?this._t("balance.export"):this._t("balance.grid")} <b>${he(Math.abs(n))}</b></span>`),o!==null){let g=o>50?"+ ":o<-50?"\u2212 ":"",y=Math.abs(o)<=50?this._t("balance.idle"):`${g}${he(Math.abs(o))}`,x=c!=null?` \xB7 ${Math.round(w(c))} %${Number.isNaN(l)?"":` \xB7 ${this._t("balance.reserve",{pct:String(Math.round(l))})}`}`:"",z=u?d`<ha-icon class="hold-ico" icon="mdi:shield"></ha-icon>`:h;p.push(d`<span><i class="dot" style="background:var(--goe-battery)"></i>${this._t("balance.battery")} <b>${y}</b>${x}${z}</span>`)}return d`<div class="balance">${p}</div>`}_renderChips(e){let t=this._stateObj(e.status)?.attributes??{},r=[];if(this._holdActive(e)){let p=(t.hold_source??"auto")==="hold";r.push(this._chip("mdi:shield",p?"chip.hold_manual":"chip.hold",{},"hold"))}let i=this._stateObj(e.price_forecast);if(i&&!["unknown","unavailable",""].includes(i.state)){let p=w(i.state),g=this._cheapTarget(e),y=i.attributes.unit??"";if(!Number.isNaN(p)){let x=!Number.isNaN(g)&&p<=g;r.push(this._chip("mdi:cash-clock",x?"chip.price_cheap":"chip.price_wait",{price:this._fmtPriceNum(p),unit:y,target:this._fmtPriceNum(g)},x?"cheap":""))}}let n=this._countdown(t.resume_not_before);if(n!==null){let p={time:$e(n)};r.push(this._canStartNow(e)?this._actionChip("mdi:play-speed","chip.resume_in",p,"chip.start_now",()=>this._startNow(e)):this._chip("mdi:clock-outline","chip.resume_in",p))}let o=this._countdown(t.pause_not_before);o!==null&&r.push(this._chip("mdi:clock-outline","chip.riding_out",{time:$e(o)})),t.forced===!1&&r.push(this._chip("mdi:hand-back-left","chip.forced_off",{},"hold"));let c=this._stateObj(e.peak_window_power),l=String(c?.attributes?.tier??"off");l==="soft"||l==="hard"?r.push(this._chip("mdi:transmission-tower-off",l==="hard"?"chip.peak_hard":"chip.peak_soft",{projected:this._fmtKwNum(w(c?.attributes?.projected_w))},"hold")):c?.attributes?.degraded===!0&&c.attributes.enabled===!0&&r.push(this._chip("mdi:progress-question","chip.peak_degraded",{}));let u=this._stateObj(e.peak_status);return u?.attributes?.grid_charging===!0&&r.push(this._chip("mdi:cash-clock","chip.grid_charging",{power:ct(w(u.attributes.grid_setpoint_w))},"cheap")),r.length===0?d``:d`<div class="chips">${r}</div>`}_chip(e,t,r,i=""){return d`<span class="chipx ${i}"><ha-icon icon="${e}"></ha-icon>${this._t(t,r)}</span>`}_actionChip(e,t,r,i,n){return d`<button class="chipx act" @click=${n}>
      <ha-icon icon="${e}"></ha-icon>${this._t(t,r)}
      <span class="cta">${this._t(i)}</span>
    </button>`}_canStartNow(e){let t=this._stateObj(e.start_now);return!!t&&t.state!=="unavailable"}_startNow(e){e.start_now&&this.hass.callService("button","press",{entity_id:e.start_now})}_renderPlan(e){if(this._effectiveState(e.charging_mode)!=="smart")return h;let r=this._stateObj(e.status)?.attributes??{},i=new Set(r.plan??[]),n=this._planLine(e,i.size);return n===h?h:d`<div class="plan">${n}</div>`}_planLine(e,t){let r=w(this._stateObj(e.target_energy)?.state);if(Number.isNaN(r)||r<=0)return h;let i=w((this._stateObj(e.power_flow)?.attributes??{}).session_energy_kwh),n=Number.isNaN(i)?0:i,o=Math.min(100,Math.round(n/r*100)),c=t>=4?this._t("plan.on_track"):this._t("plan.tight");return d`
      <div class="planline">
        <b>${n.toFixed(1)} / ${r.toFixed(0)} kWh</b> — ${c}
      </div>
      <div class="progress"><i style="width:${o}%"></i></div>`}_renderControls(e){let t=this._stateObj(e.charging_mode),r=this._effectiveState(e.charging_mode),i=r==="manual",n=r?`mode_hint.${r}`:"",o=n?this._t(n):"";return d`<div class="controls">
      ${t?this._renderModeSeg(e,t):h}
      ${o&&o!==n?d`<div class="modehint">${o}</div>`:h}
      <div class="ctxctl">
        ${i?this._renderManual(e):this._renderModeTunables(e,r)}
        ${this._renderBatteryThreeWay(e)}
        ${this._renderNumberRow(e.battery_reserve_soc,"control.battery_reserve")}
      </div>
    </div>`}_renderModeSeg(e,t){let r=t.attributes.options??[],i=this._effectiveState(e.charging_mode),n={manual:"mdi:hand-back-right",solar:"mdi:solar-power",solar_min:"mdi:solar-power-variant",smart:"mdi:brain",fast:"mdi:flash"};return d`<div class="seg">
      ${r.map(o=>d`<button
          class="${o===i?"on":""}"
          @click=${()=>this._selectOptimistic(t,o)}
        >
          <ha-icon icon="${n[o]??"mdi:ev-station"}"></ha-icon>
          <span>${this._localizeOption(t,o)}</span>
        </button>`)}
    </div>`}_renderModeTunables(e,t){return d`
      ${t==="smart"?d`${this._renderNumberRow(e.target_energy,"control.target_energy")}
            ${this._renderDateTimeRow(e.departure,"control.departure")}`:h}
      ${t==="solar_min"?this._renderNumberRow(e.min_current,"control.min_current"):h}
      ${t==="fast"?this._renderNumberRow(e.max_current,"control.max_current"):h}
      ${e.auto_phase?d`<div class="ctlrow">
            <label>${this._t("control.auto_phase")}</label>
            <ha-switch
              .checked=${this._isOn(e.auto_phase)}
              @change=${r=>this._toggle(e.auto_phase,r)}
            ></ha-switch>
          </div>`:h}`}_renderManual(e){let t=this._isOn(e.manual_charge);return d`
      ${e.manual_charge?d`<button
            class="bigbtn ${t?"stop":""}"
            @click=${()=>this._toggleManualCharge(e,t)}
          >
            <ha-icon icon="${t?"mdi:stop":"mdi:play"}"></ha-icon>
            ${t?this._t("action.stop_charging"):this._t("action.start_charging")}
          </button>`:h}
      ${this._renderNumberRow(e.manual_current,"control.manual_current")}
      ${e.manual_phases?d`<div class="ctlrow">
            <label>${this._t("control.manual_phases")}</label>
            ${this._renderSelect(this._stateObj(e.manual_phases))}
          </div>`:h}`}_renderBatteryThreeWay(e){let t=this._stateObj(e.battery_hold_mode);if(!t)return h;let r=t.attributes.options??["auto","hold","free"],i=this._effectiveState(e.battery_hold_mode),n=this._holdActive(e);return d`<div class="ctlrow">
      <label>${this._t("control.home_battery")}</label>
      <span class="minisg">
        ${r.map(o=>d`<button
            class="${o===i?"on":""}"
            @click=${()=>this._selectOptimistic(t,o)}
          >
            ${this._localizeOption(t,o)}${o==="auto"&&n&&i==="auto"?d`<ha-icon class="hold-ico" icon="mdi:shield"></ha-icon>`:h}
          </button>`)}
      </span>
    </div>`}_renderNumberRow(e,t){let r=this._stateObj(e);return r?d`<div class="ctlrow">
      <label>${this._t(t)}</label>
      ${this._renderNumber(r)}
    </div>`:h}_renderDateTimeRow(e,t){let r=this._stateObj(e);return r?d`<div class="ctlrow">
      <label>${this._t(t)}</label>
      ${this._renderDateTime(r)}
    </div>`:h}_renderSession(e){let t=this._stateObj(e.active_transaction),r=this._stateObj(e.selected_tag);if(!t&&!r)return h;let i=!!t&&!["idle","unknown","unavailable",""].includes(t.state),n=this._stateObj(e.power_flow)?.attributes??{},o=w(n.session_energy_kwh),c="";if(i&&t){let l=t.attributes.name??t.state,u=this._liveDuration(t.attributes.started),p=[];u&&p.push(u),!Number.isNaN(o)&&o>0&&p.push(`${o.toFixed(2)} kWh`),c=d`<b>${l}</b>${p.length?d` · <span class="mono">${p.join(" \xB7 ")}</span>`:h}`}return d`<div class="session">
      ${this._renderTagPicker(r,i)}
      <div class="session-row">
        <ha-icon icon="mdi:card-account-details"></ha-icon>
        <span>${i?c:this._t("session.none_hint")}</span>
      </div>
    </div>`}_renderTagPicker(e,t){if(!e)return h;let r=e.attributes.options??[];if(r.length===0)return h;let i=r.includes(e.state);return d`<div class="tag-picker">
      ${t?h:d`<div class="ctlrow">
            <label>${this._t("control.tag")}</label>
            ${this._renderSelect(e)}
          </div>`}
      <div class="tag-actions">
        ${t?d`<button class="bigbtn stop" @click=${()=>this._confirmStop()}>
              <ha-icon icon="mdi:stop"></ha-icon>${this._t("action.stop")}
            </button>`:d`<button
              class="bigbtn"
              ?disabled=${!i}
              @click=${()=>this._callTagService("remote_start")}
            >
              <ha-icon icon="mdi:play"></ha-icon>${this._t("action.start")}
            </button>`}
      </div>
    </div>`}_statusReason(e){let t=e?.state&&e.state!=="unknown"?e.state:"\u2014",r=e?.attributes?.reason_key;if(!r)return t;let i=`reason.${r}`,n=e?.attributes?.reason_params??{},o=this._t(i,this._localizeNumbers(n));return o===i?t:o}_localizeNumbers(e){let t=(this.hass?.locale?.language||this.hass?.language||"en").toLowerCase().split("-")[0],r={};for(let[i,n]of Object.entries(e)){let o=/^-?\d+(?:\.(\d+))?$/.exec(n);if(o){let c=o[1]?.length??0;r[i]=new Intl.NumberFormat(t,{minimumFractionDigits:c,maximumFractionDigits:c}).format(Number(n))}else r[i]=n}return r}_renderNumber(e){let t=e.attributes,r=t.unit_of_measurement??"";return d`<span class="ctl-number-wrap">
      <input
        class="ctl-number"
        type="number"
        .value=${e.state}
        min=${t.min??h}
        max=${t.max??h}
        step=${t.step??h}
        @change=${i=>this._setNumber(e,i.target.value)}
      />
      ${r?d`<span class="ctl-unit">${r}</span>`:h}
    </span>`}_setNumber(e,t){let r=Number(t);Number.isNaN(r)||String(r)===e.state||this.hass.callService("number","set_value",{entity_id:e.entity_id,value:r})}_renderDateTime(e){return d`<input
      class="ctl-datetime"
      type="datetime-local"
      .value=${this._toLocalInput(e.state)}
      @change=${t=>this._setDateTime(e,t.target.value)}
    />`}_toLocalInput(e){let t=new Date(e);if(Number.isNaN(t.getTime()))return"";let r=i=>String(i).padStart(2,"0");return`${t.getFullYear()}-${r(t.getMonth()+1)}-${r(t.getDate())}T${r(t.getHours())}:${r(t.getMinutes())}`}_setDateTime(e,t){if(!t)return;let r=new Date(t);Number.isNaN(r.getTime())||this.hass.callService("datetime","set_value",{entity_id:e.entity_id,datetime:r.toISOString()})}_renderSelect(e){let t=e.attributes.options??[];return d`<select
      class="ctl-select"
      @change=${r=>this._selectOption(e,r.target.value)}
    >
      ${t.map(r=>d`<option .value=${r} ?selected=${r===e.state}>
          ${this._localizeOption(e,r)}
        </option>`)}
    </select>`}_callTagService(e){this.hass.callService(T,e,{})}_confirmStop(){window.confirm(this._t("action.stop_confirm"))&&this._callTagService("remote_stop")}_toggleManualCharge(e,t){e.manual_charge&&this.hass.callService("switch",t?"turn_off":"turn_on",{entity_id:e.manual_charge})}_sourceShares(e){let t=e.sources??{},r=Math.max(0,w(t.solar_w)||0),i=Math.max(0,w(t.battery_w)||0),n=Math.max(0,w(t.grid_w)||0);return{solar:r,battery:i,grid:n,total:r+i+n}}_cheapTarget(e){let t=this._stateObj(e.price_forecast),r=w(t?.attributes?.cheap_price);return Number.isNaN(r)?w(this._stateObj(e.cheap_price)?.state):r}_holdActive(e){let t=(this._stateObj(e.status)?.attributes??{}).hold_battery;return typeof t=="boolean"?t:this._isOn(e.battery_hold)}_countdown(e){if(typeof e!="string")return null;let t=Date.parse(e);if(Number.isNaN(t))return null;let r=(t-this._now)/1e3;return r>0?r:null}_ageSeconds(e){if(!e?.last_updated)return null;let t=Date.parse(e.last_updated);return Number.isNaN(t)?null:Math.max(0,(this._now-t)/1e3)}_fmtAgo(e){return e<90?`${Math.round(e)} s`:`${Math.round(e/60)} min`}_liveDuration(e){if(!e)return"";let t=Date.parse(e);return Number.isNaN(t)?"":$e((this._now-t)/1e3)}_fmtPriceNum(e){return Number.isNaN(e)?"\u2014":Number.isInteger(e)?String(e):e.toFixed(e<1?2:1)}_fmtKwNum(e){return Number.isNaN(e)?"\u2014":(e/1e3).toFixed(2)}_effectiveState(e){let t=this._stateObj(e)?.state;if(!e)return t;let r=this._optimistic.get(e);return r?t===r.value||Date.now()-r.at>4e3?(this._optimistic.delete(e),t):r.value:t}_selectOptimistic(e,t){t!==e.state&&(this._optimistic.set(e.entity_id,{value:t,at:Date.now()}),this.requestUpdate(),this.hass.callService("select","select_option",{entity_id:e.entity_id,option:t}))}_stateObj(e){return e?this.hass.states[e]:void 0}_isOn(e){return this._stateObj(e)?.state==="on"}_localizeOption(e,t){let r=this.hass.entities?.[e.entity_id]?.translation_key;if(r){let i=`component.${T}.entity.select.${r}.state.${t}`,n=this.hass.localize?.(i);if(n)return n}if(this.hass.formatEntityState){let i=this.hass.formatEntityState({...e,state:t},t);if(i)return i}return t}_deviceName(e){let t=this.hass.devices[e];return t?.name_by_user||t?.name||null}_selectOption(e,t){t!==e.state&&this.hass.callService("select","select_option",{entity_id:e.entity_id,option:t})}_toggle(e,t){if(!e)return;let r=t.target.checked;this.hass.callService("switch",r?"turn_on":"turn_off",{entity_id:e})}};L.styles=[we,S`
    :host {
      --goe-solar: #dd9a16;
      --goe-battery: var(--success-color, #3f9e68);
      --goe-grid: #67789c;
      --goe-accent: var(--primary-color);
      --goe-chip: var(--secondary-background-color);
    }
    ha-card {
      overflow: hidden;
    }
    .empty {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 8px;
      padding: 24px;
      color: var(--secondary-text-color);
      text-align: center;
    }
    .empty ha-icon {
      --mdc-icon-size: 40px;
      color: var(--disabled-text-color);
    }
    .mono {
      font-variant-numeric: tabular-nums;
    }
    .hacard {
      display: flex;
      flex-direction: column;
      gap: 14px;
      padding: 14px 16px 16px;
    }

    /* Header */
    .c-head {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .c-title {
      font-weight: 600;
      font-size: 1.05rem;
    }
    .brain {
      color: var(--goe-accent);
    }
    .brain.off {
      color: var(--disabled-text-color);
    }
    .livedot {
      margin-left: auto;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 0.72rem;
      color: var(--secondary-text-color);
    }
    .livedot i {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--goe-battery);
    }
    .livedot.stale i {
      background: var(--disabled-text-color);
    }
    @media (prefers-reduced-motion: no-preference) {
      .livedot:not(.stale) i {
        animation: pulse 2s ease-in-out infinite;
      }
      @keyframes pulse {
        50% {
          opacity: 0.35;
        }
      }
    }

    /* Hero */
    .c-hero {
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .ringwrap {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 5px;
      flex: none;
    }
    .ring {
      width: 92px;
      height: 92px;
      flex: none;
      position: relative;
    }
    .solarbadge {
      display: inline-flex;
      align-items: center;
      gap: 3px;
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--goe-solar);
      font-variant-numeric: tabular-nums;
    }
    .solarbadge ha-icon {
      --mdc-icon-size: 14px;
    }
    .ring svg {
      width: 100%;
      height: 100%;
      transform: rotate(-90deg);
    }
    .ring .track {
      stroke: var(--divider-color);
    }
    .ring circle {
      transition: stroke-dasharray 0.5s ease, stroke-dashoffset 0.5s ease;
    }
    .caric {
      position: absolute;
      inset: 0;
      display: grid;
      place-items: center;
    }
    .caric ha-icon {
      --mdc-icon-size: 34px;
      color: var(--secondary-text-color);
    }
    .ring.on .caric ha-icon {
      color: var(--primary-text-color);
    }
    .power {
      font-size: 2.1rem;
      font-weight: 600;
      line-height: 1;
      font-variant-numeric: tabular-nums;
    }
    .power small {
      font-size: 1.05rem;
      font-weight: 500;
      color: var(--secondary-text-color);
    }
    .herosub {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
      margin-top: 5px;
      font-variant-numeric: tabular-nums;
    }

    .why {
      font-size: 0.9rem;
      color: var(--primary-text-color);
      min-height: 1.2em;
    }
    .why b {
      color: var(--goe-accent);
    }

    /* Source bar + balance */
    .splitbar {
      display: flex;
      height: 26px;
      border-radius: 8px;
      overflow: hidden;
      gap: 2px;
      background: var(--goe-chip);
    }
    .seg-src {
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-size: 0.72rem;
      font-weight: 600;
      min-width: 0;
      overflow: hidden;
      white-space: nowrap;
      border: 0;
      cursor: pointer;
      padding: 0;
      font-family: inherit;
      transition: flex-grow 0.6s ease;
    }
    .seg-src.solar {
      background: var(--goe-solar);
    }
    .seg-src.battery {
      background: var(--goe-battery);
    }
    .seg-src.grid {
      background: var(--goe-grid);
    }
    @media (prefers-reduced-motion: no-preference) {
      .splitbar.flowing .seg-src {
        background-image: linear-gradient(
          100deg,
          rgba(255, 255, 255, 0) 40%,
          rgba(255, 255, 255, 0.28) 50%,
          rgba(255, 255, 255, 0) 60%
        );
        background-size: 220% 100%;
        animation: sheen 2.6s linear infinite;
      }
      @keyframes sheen {
        from {
          background-position: 130% 0;
        }
        to {
          background-position: -90% 0;
        }
      }
    }
    .splitnote {
      font-size: 0.74rem;
      color: var(--secondary-text-color);
      margin-top: 6px;
      min-height: 1.1em;
      font-variant-numeric: tabular-nums;
    }
    .balance {
      display: flex;
      flex-wrap: wrap;
      gap: 4px 14px;
      margin-top: 4px;
      font-size: 0.78rem;
      color: var(--secondary-text-color);
      font-variant-numeric: tabular-nums;
    }
    .balance b {
      color: var(--primary-text-color);
    }
    .balance .dot {
      width: 8px;
      height: 8px;
      border-radius: 3px;
      display: inline-block;
      margin-right: 5px;
    }
    .hold-ico {
      --mdc-icon-size: 14px;
      color: var(--warning-color, #c05252);
      margin-left: 4px;
      vertical-align: -2px;
    }

    /* Chips */
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .chipx {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: var(--goe-chip);
      border-radius: 999px;
      padding: 4px 11px;
      font-size: 0.76rem;
      font-weight: 500;
      color: var(--primary-text-color);
      border: 1px solid transparent;
      font-variant-numeric: tabular-nums;
    }
    .chipx ha-icon {
      --mdc-icon-size: 15px;
      color: var(--secondary-text-color);
    }
    .chipx.hold {
      border-color: var(--warning-color, #c05252);
      color: var(--warning-color, #c05252);
    }
    .chipx.hold ha-icon {
      color: var(--warning-color, #c05252);
    }
    .chipx.cheap {
      border-color: var(--goe-battery);
    }
    .chipx.cheap ha-icon {
      color: var(--goe-battery);
    }
    /* Actionable chip: reads as a chip, behaves as a button. */
    button.chipx {
      font-family: inherit;
      cursor: pointer;
      border-color: var(--primary-color);
    }
    button.chipx:hover {
      background: var(--goe-chip-hover, var(--secondary-background-color));
    }
    button.chipx ha-icon,
    button.chipx .cta {
      color: var(--primary-color);
    }
    button.chipx .cta {
      font-weight: 600;
    }

    /* Plan strip: charging-progress line */
    .planline {
      font-size: 0.78rem;
      color: var(--secondary-text-color);
      margin-top: 6px;
      font-variant-numeric: tabular-nums;
    }
    .planline b {
      color: var(--primary-text-color);
    }
    .progress {
      height: 5px;
      border-radius: 999px;
      background: var(--goe-chip);
      margin-top: 6px;
      overflow: hidden;
    }
    .progress i {
      display: block;
      height: 100%;
      background: var(--goe-accent);
      border-radius: 999px;
      transition: width 0.5s ease;
    }

    /* Controls */
    .controls {
      border-top: 1px solid var(--divider-color);
      padding-top: 12px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .ctxctl {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .seg {
      display: flex;
      background: var(--goe-chip);
      border-radius: 12px;
      padding: 3px;
      gap: 2px;
    }
    .seg button {
      flex: 1;
      border: 0;
      background: transparent;
      border-radius: 9px;
      padding: 7px 2px 5px;
      cursor: pointer;
      color: var(--secondary-text-color);
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
      font-family: inherit;
      font-size: 0.64rem;
      font-weight: 600;
    }
    .seg button ha-icon {
      --mdc-icon-size: 17px;
    }
    .seg button.on {
      background: var(--card-background-color);
      color: var(--goe-accent);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
    }
    .modehint {
      font-size: 0.78rem;
      color: var(--secondary-text-color);
      margin-top: -2px;
    }
    .ctlrow {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .ctlrow label {
      font-size: 0.85rem;
      color: var(--secondary-text-color);
      white-space: nowrap;
    }
    .minisg {
      display: inline-flex;
      background: var(--goe-chip);
      border-radius: 10px;
      padding: 2px;
      gap: 2px;
    }
    .minisg button {
      border: 0;
      background: transparent;
      border-radius: 8px;
      padding: 5px 13px;
      font: inherit;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--secondary-text-color);
      cursor: pointer;
    }
    .minisg button.on {
      background: var(--card-background-color);
      color: var(--goe-accent);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
    }
    .bigbtn {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      border: 0;
      border-radius: 12px;
      padding: 12px;
      width: 100%;
      font: inherit;
      font-size: 0.92rem;
      font-weight: 600;
      cursor: pointer;
      background: var(--goe-accent);
      color: var(--text-primary-color, #fff);
    }
    .bigbtn ha-icon {
      --mdc-icon-size: 18px;
    }
    .bigbtn.stop {
      background: color-mix(in srgb, var(--error-color, #db4437) 14%, var(--card-background-color));
      color: var(--error-color, #db4437);
      border: 1px solid var(--error-color, #db4437);
    }
    .bigbtn[disabled] {
      opacity: 0.5;
      cursor: default;
    }

    /* Inputs */
    .ctl-select,
    .ctl-datetime {
      min-width: 150px;
      max-width: 60%;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--ha-card-background));
      color: var(--primary-text-color);
      font-family: inherit;
      font-size: 0.9rem;
      cursor: pointer;
    }
    .ctl-select:focus,
    .ctl-datetime:focus,
    .ctl-number:focus {
      outline: none;
      border-color: var(--goe-accent);
    }
    .ctl-number-wrap {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      justify-content: flex-end;
    }
    .ctl-number {
      width: 90px;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--ha-card-background));
      color: var(--primary-text-color);
      font-family: inherit;
      font-size: 0.9rem;
      text-align: right;
    }
    .ctl-unit {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
      white-space: nowrap;
    }

    /* Session */
    .session {
      border-top: 1px solid var(--divider-color);
      padding-top: 10px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .session-row {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.85rem;
      color: var(--primary-text-color);
      font-variant-numeric: tabular-nums;
    }
    .session-row ha-icon {
      --mdc-icon-size: 16px;
      color: var(--secondary-text-color);
    }
    .tag-picker {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .tag-actions {
      display: flex;
      gap: 8px;
    }
    .peakstrip {
      margin-top: -4px;
    }
    :focus-visible {
      outline: 2px solid var(--goe-accent);
      outline-offset: 2px;
    }
  `],_([N({attribute:!1})],L.prototype,"hass",2),_([k()],L.prototype,"_config",2),_([k()],L.prototype,"_now",2),_([k()],L.prototype,"_optimistic",2),L=_([R("goe-steve-card")],L);window.customCards=window.customCards||[];window.customCards.push({type:"goe-steve-card",name:"go-e + SteVe Smart Charging",description:"Live source split, the brain's reasoning, plan strip and inline controls for smart EV charging.",preview:!0,documentationURL:"https://github.com/JustChr/HAgoe_steve"});export{L as GoeSteveCard};
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
lit-html/lit-html.js:
lit-element/lit-element.js:
@lit/reactive-element/decorators/custom-element.js:
@lit/reactive-element/decorators/property.js:
@lit/reactive-element/decorators/state.js:
@lit/reactive-element/decorators/event-options.js:
@lit/reactive-element/decorators/base.js:
@lit/reactive-element/decorators/query.js:
@lit/reactive-element/decorators/query-all.js:
@lit/reactive-element/decorators/query-async.js:
@lit/reactive-element/decorators/query-assigned-nodes.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-assigned-elements.js:
  (**
   * @license
   * Copyright 2021 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/directives/if-defined.js:
  (**
   * @license
   * Copyright 2018 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
