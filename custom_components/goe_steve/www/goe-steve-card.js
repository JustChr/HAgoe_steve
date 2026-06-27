/* go-e + SteVe Smart Charging card — bundled, do not edit by hand. Source in /card. */
var Jt=Object.defineProperty;var Yt=Object.getOwnPropertyDescriptor;var y=(o,t,e,s)=>{for(var r=s>1?void 0:s?Yt(t,e):t,i=o.length-1,n;i>=0;i--)(n=o[i])&&(r=(s?n(t,e,r):n(r))||r);return s&&r&&Jt(t,e,r),r};var nt=globalThis,ot=nt.ShadowRoot&&(nt.ShadyCSS===void 0||nt.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,gt=Symbol(),Rt=new WeakMap,J=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==gt)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(ot&&t===void 0){let s=e!==void 0&&e.length===1;s&&(t=Rt.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&Rt.set(e,t))}return t}toString(){return this.cssText}},Mt=o=>new J(typeof o=="string"?o:o+"",void 0,gt),E=(o,...t)=>{let e=o.length===1?o[0]:t.reduce((s,r,i)=>s+(n=>{if(n._$cssResult$===!0)return n.cssText;if(typeof n=="number")return n;throw Error("Value passed to 'css' function must be a 'css' function result: "+n+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(r)+o[i+1],o[0]);return new J(e,o,gt)},Tt=(o,t)=>{if(ot)o.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let s=document.createElement("style"),r=nt.litNonce;r!==void 0&&s.setAttribute("nonce",r),s.textContent=e.cssText,o.appendChild(s)}},mt=ot?o=>o:o=>o instanceof CSSStyleSheet?(t=>{let e="";for(let s of t.cssRules)e+=s.cssText;return Mt(e)})(o):o;var{is:Zt,defineProperty:Gt,getOwnPropertyDescriptor:Xt,getOwnPropertyNames:Qt,getOwnPropertySymbols:te,getPrototypeOf:ee}=Object,at=globalThis,Ht=at.trustedTypes,se=Ht?Ht.emptyScript:"",re=at.reactiveElementPolyfillSupport,Y=(o,t)=>o,Z={toAttribute(o,t){switch(t){case Boolean:o=o?se:null;break;case Object:case Array:o=o==null?o:JSON.stringify(o)}return o},fromAttribute(o,t){let e=o;switch(t){case Boolean:e=o!==null;break;case Number:e=o===null?null:Number(o);break;case Object:case Array:try{e=JSON.parse(o)}catch{e=null}}return e}},ct=(o,t)=>!Zt(o,t),Pt={attribute:!0,type:String,converter:Z,reflect:!1,useDefault:!1,hasChanged:ct};Symbol.metadata??=Symbol("metadata"),at.litPropertyMetadata??=new WeakMap;var C=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=Pt){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let s=Symbol(),r=this.getPropertyDescriptor(t,s,e);r!==void 0&&Gt(this.prototype,t,r)}}static getPropertyDescriptor(t,e,s){let{get:r,set:i}=Xt(this.prototype,t)??{get(){return this[e]},set(n){this[e]=n}};return{get:r,set(n){let a=r?.call(this);i?.call(this,n),this.requestUpdate(t,a,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??Pt}static _$Ei(){if(this.hasOwnProperty(Y("elementProperties")))return;let t=ee(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(Y("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(Y("properties"))){let e=this.properties,s=[...Qt(e),...te(e)];for(let r of s)this.createProperty(r,e[r])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[s,r]of e)this.elementProperties.set(s,r)}this._$Eh=new Map;for(let[e,s]of this.elementProperties){let r=this._$Eu(e,s);r!==void 0&&this._$Eh.set(r,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let s=new Set(t.flat(1/0).reverse());for(let r of s)e.unshift(mt(r))}else t!==void 0&&e.push(mt(t));return e}static _$Eu(t,e){let s=e.attribute;return s===!1?void 0:typeof s=="string"?s:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return Tt(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){let s=this.constructor.elementProperties.get(t),r=this.constructor._$Eu(t,s);if(r!==void 0&&s.reflect===!0){let i=(s.converter?.toAttribute!==void 0?s.converter:Z).toAttribute(e,s.type);this._$Em=t,i==null?this.removeAttribute(r):this.setAttribute(r,i),this._$Em=null}}_$AK(t,e){let s=this.constructor,r=s._$Eh.get(t);if(r!==void 0&&this._$Em!==r){let i=s.getPropertyOptions(r),n=typeof i.converter=="function"?{fromAttribute:i.converter}:i.converter?.fromAttribute!==void 0?i.converter:Z;this._$Em=r;let a=n.fromAttribute(e,i.type);this[r]=a??this._$Ej?.get(r)??a,this._$Em=null}}requestUpdate(t,e,s,r=!1,i){if(t!==void 0){let n=this.constructor;if(r===!1&&(i=this[t]),s??=n.getPropertyOptions(t),!((s.hasChanged??ct)(i,e)||s.useDefault&&s.reflect&&i===this._$Ej?.get(t)&&!this.hasAttribute(n._$Eu(t,s))))return;this.C(t,e,s)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:r,wrapped:i},n){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,n??e??this[t]),i!==!0||n!==void 0)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),r===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[r,i]of this._$Ep)this[r]=i;this._$Ep=void 0}let s=this.constructor.elementProperties;if(s.size>0)for(let[r,i]of s){let{wrapped:n}=i,a=this[r];n!==!0||this._$AL.has(r)||a===void 0||this.C(r,void 0,i,a)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(s=>s.hostUpdate?.()),this.update(e)):this._$EM()}catch(s){throw t=!1,this._$EM(),s}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};C.elementStyles=[],C.shadowRootOptions={mode:"open"},C[Y("elementProperties")]=new Map,C[Y("finalized")]=new Map,re?.({ReactiveElement:C}),(at.reactiveElementVersions??=[]).push("2.1.2");var xt=globalThis,zt=o=>o,lt=xt.trustedTypes,Ot=lt?lt.createPolicy("lit-html",{createHTML:o=>o}):void 0,It="$lit$",T=`lit$${Math.random().toFixed(9).slice(2)}$`,Bt="?"+T,ie=`<${Bt}>`,j=document,X=()=>j.createComment(""),Q=o=>o===null||typeof o!="object"&&typeof o!="function",wt=Array.isArray,ne=o=>wt(o)||typeof o?.[Symbol.iterator]=="function",_t=`[ 	
\f\r]`,G=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,Lt=/-->/g,jt=/>/g,O=RegExp(`>|${_t}(?:([^\\s"'>=/]+)(${_t}*=${_t}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),Ut=/'/g,Dt=/"/g,Ft=/^(?:script|style|textarea|title)$/i,At=o=>(t,...e)=>({_$litType$:o,strings:t,values:e}),d=At(1),k=At(2),xe=At(3),U=Symbol.for("lit-noChange"),l=Symbol.for("lit-nothing"),Wt=new WeakMap,L=j.createTreeWalker(j,129);function qt(o,t){if(!wt(o)||!o.hasOwnProperty("raw"))throw Error("invalid template strings array");return Ot!==void 0?Ot.createHTML(t):t}var oe=(o,t)=>{let e=o.length-1,s=[],r,i=t===2?"<svg>":t===3?"<math>":"",n=G;for(let a=0;a<e;a++){let c=o[a],p,u,h=-1,g=0;for(;g<c.length&&(n.lastIndex=g,u=n.exec(c),u!==null);)g=n.lastIndex,n===G?u[1]==="!--"?n=Lt:u[1]!==void 0?n=jt:u[2]!==void 0?(Ft.test(u[2])&&(r=RegExp("</"+u[2],"g")),n=O):u[3]!==void 0&&(n=O):n===O?u[0]===">"?(n=r??G,h=-1):u[1]===void 0?h=-2:(h=n.lastIndex-u[2].length,p=u[1],n=u[3]===void 0?O:u[3]==='"'?Dt:Ut):n===Dt||n===Ut?n=O:n===Lt||n===jt?n=G:(n=O,r=void 0);let _=n===O&&o[a+1].startsWith("/>")?" ":"";i+=n===G?c+ie:h>=0?(s.push(p),c.slice(0,h)+It+c.slice(h)+T+_):c+T+(h===-2?a:_)}return[qt(o,i+(o[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),s]},tt=class o{constructor({strings:t,_$litType$:e},s){let r;this.parts=[];let i=0,n=0,a=t.length-1,c=this.parts,[p,u]=oe(t,e);if(this.el=o.createElement(p,s),L.currentNode=this.el.content,e===2||e===3){let h=this.el.content.firstChild;h.replaceWith(...h.childNodes)}for(;(r=L.nextNode())!==null&&c.length<a;){if(r.nodeType===1){if(r.hasAttributes())for(let h of r.getAttributeNames())if(h.endsWith(It)){let g=u[n++],_=r.getAttribute(h).split(T),m=/([.?@])?(.*)/.exec(g);c.push({type:1,index:i,name:m[2],strings:_,ctor:m[1]==="."?vt:m[1]==="?"?yt:m[1]==="@"?bt:F}),r.removeAttribute(h)}else h.startsWith(T)&&(c.push({type:6,index:i}),r.removeAttribute(h));if(Ft.test(r.tagName)){let h=r.textContent.split(T),g=h.length-1;if(g>0){r.textContent=lt?lt.emptyScript:"";for(let _=0;_<g;_++)r.append(h[_],X()),L.nextNode(),c.push({type:2,index:++i});r.append(h[g],X())}}}else if(r.nodeType===8)if(r.data===Bt)c.push({type:2,index:i});else{let h=-1;for(;(h=r.data.indexOf(T,h+1))!==-1;)c.push({type:7,index:i}),h+=T.length-1}i++}}static createElement(t,e){let s=j.createElement("template");return s.innerHTML=t,s}};function B(o,t,e=o,s){if(t===U)return t;let r=s!==void 0?e._$Co?.[s]:e._$Cl,i=Q(t)?void 0:t._$litDirective$;return r?.constructor!==i&&(r?._$AO?.(!1),i===void 0?r=void 0:(r=new i(o),r._$AT(o,e,s)),s!==void 0?(e._$Co??=[])[s]=r:e._$Cl=r),r!==void 0&&(t=B(o,r._$AS(o,t.values),r,s)),t}var ft=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:s}=this._$AD,r=(t?.creationScope??j).importNode(e,!0);L.currentNode=r;let i=L.nextNode(),n=0,a=0,c=s[0];for(;c!==void 0;){if(n===c.index){let p;c.type===2?p=new et(i,i.nextSibling,this,t):c.type===1?p=new c.ctor(i,c.name,c.strings,this,t):c.type===6&&(p=new $t(i,this,t)),this._$AV.push(p),c=s[++a]}n!==c?.index&&(i=L.nextNode(),n++)}return L.currentNode=j,r}p(t){let e=0;for(let s of this._$AV)s!==void 0&&(s.strings!==void 0?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}},et=class o{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,r){this.type=2,this._$AH=l,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=B(this,t,e),Q(t)?t===l||t==null||t===""?(this._$AH!==l&&this._$AR(),this._$AH=l):t!==this._$AH&&t!==U&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):ne(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==l&&Q(this._$AH)?this._$AA.nextSibling.data=t:this.T(j.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:s}=t,r=typeof s=="number"?this._$AC(t):(s.el===void 0&&(s.el=tt.createElement(qt(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===r)this._$AH.p(e);else{let i=new ft(r,this),n=i.u(this.options);i.p(e),this.T(n),this._$AH=i}}_$AC(t){let e=Wt.get(t.strings);return e===void 0&&Wt.set(t.strings,e=new tt(t)),e}k(t){wt(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,s,r=0;for(let i of t)r===e.length?e.push(s=new o(this.O(X()),this.O(X()),this,this.options)):s=e[r],s._$AI(i),r++;r<e.length&&(this._$AR(s&&s._$AB.nextSibling,r),e.length=r)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let s=zt(t).nextSibling;zt(t).remove(),t=s}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},F=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,r,i){this.type=1,this._$AH=l,this._$AN=void 0,this.element=t,this.name=e,this._$AM=r,this.options=i,s.length>2||s[0]!==""||s[1]!==""?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=l}_$AI(t,e=this,s,r){let i=this.strings,n=!1;if(i===void 0)t=B(this,t,e,0),n=!Q(t)||t!==this._$AH&&t!==U,n&&(this._$AH=t);else{let a=t,c,p;for(t=i[0],c=0;c<i.length-1;c++)p=B(this,a[s+c],e,c),p===U&&(p=this._$AH[c]),n||=!Q(p)||p!==this._$AH[c],p===l?t=l:t!==l&&(t+=(p??"")+i[c+1]),this._$AH[c]=p}n&&!r&&this.j(t)}j(t){t===l?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},vt=class extends F{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===l?void 0:t}},yt=class extends F{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==l)}},bt=class extends F{constructor(t,e,s,r,i){super(t,e,s,r,i),this.type=5}_$AI(t,e=this){if((t=B(this,t,e,0)??l)===U)return;let s=this._$AH,r=t===l&&s!==l||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,i=t!==l&&(s===l||r);r&&this.element.removeEventListener(this.name,this,s),i&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},$t=class{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){B(this,t)}};var ae=xt.litHtmlPolyfillSupport;ae?.(tt,et),(xt.litHtmlVersions??=[]).push("3.3.3");var Vt=(o,t,e)=>{let s=e?.renderBefore??t,r=s._$litPart$;if(r===void 0){let i=e?.renderBefore??null;s._$litPart$=r=new et(t.insertBefore(X(),i),i,void 0,e??{})}return r._$AI(o),r};var St=globalThis,b=class extends C{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=Vt(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return U}};b._$litElement$=!0,b.finalized=!0,St.litElementHydrateSupport?.({LitElement:b});var ce=St.litElementPolyfillSupport;ce?.({LitElement:b});(St.litElementVersions??=[]).push("4.2.2");var H=o=>(t,e)=>{e!==void 0?e.addInitializer(()=>{customElements.define(o,t)}):customElements.define(o,t)};var le={attribute:!0,type:String,converter:Z,reflect:!1,hasChanged:ct},he=(o=le,t,e)=>{let{kind:s,metadata:r}=e,i=globalThis.litPropertyMetadata.get(r);if(i===void 0&&globalThis.litPropertyMetadata.set(r,i=new Map),s==="setter"&&((o=Object.create(o)).wrapped=!0),i.set(e.name,o),s==="accessor"){let{name:n}=e;return{set(a){let c=t.get.call(this);t.set.call(this,a),this.requestUpdate(n,c,o,!0,a)},init(a){return a!==void 0&&this.C(n,void 0,o,a),a}}}if(s==="setter"){let{name:n}=e;return function(a){let c=this[n];t.call(this,a),this.requestUpdate(n,c,o,!0,a)}}throw Error("Unsupported decorator location: "+s)};function x(o){return(t,e)=>typeof e=="object"?he(o,t,e):((s,r,i)=>{let n=r.hasOwnProperty(i);return r.constructor.createProperty(i,s),n?Object.getOwnPropertyDescriptor(r,i):void 0})(o,t,e)}function N(o){return x({...o,state:!0,attribute:!1})}var R="goe_steve";function st(o){let t=new Map;for(let e of Object.values(o.entities))if(!(e.platform!==R||!e.device_id)&&!t.has(e.device_id)){let s=o.devices[e.device_id];t.set(e.device_id,s?.name_by_user||s?.name||e.device_id)}return[...t.entries()].map(([e,s])=>({id:e,name:s}))}function dt(o,t){let e={tag_energy:[]};if(!t){let i=st(o);i.length===1&&(t=i[0].id)}if(e.deviceId=t,!t)return e;let s=Object.values(o.entities).filter(i=>i.platform===R&&i.device_id===t),r=i=>{let n=s.find(c=>c.translation_key===i);return n?n.entity_id:s.find(c=>{let p=c.entity_id.split(".")[1]??"";return p===i||p.endsWith(`_${i}`)})?.entity_id};return e.status=r("status"),e.power_flow=r("power_flow"),e.surplus=r("surplus_for_car"),e.target_current=r("target_current"),e.controlling=r("controlling"),e.charging_mode=r("charging_mode"),e.battery_policy=r("battery_policy"),e.smart_control=r("smart_control"),e.auto_phase=r("auto_phase"),e.manual_charge=r("manual_charge"),e.manual_current=r("manual_current"),e.manual_phases=r("manual_phases"),e.battery_reserve_soc=r("battery_reserve_soc"),e.battery_floor_soc=r("battery_floor_soc"),e.target_energy=r("target_energy"),e.price_forecast=r("price_forecast"),e.cheap_price=r("cheap_price"),e.active_transaction=r("active_transaction"),e.last_session_energy=r("last_session_energy"),e.selected_tag=r("selected_tag"),e.tag_energy=s.filter(i=>i.translation_key==="tag_energy"||i.entity_id.split(".")[1]?.includes("_tag_energy_")).map(i=>i.entity_id).sort(),e}var Et={"card.no_device":"No {name} device found. Set one up first, then add this card.","card.default_title":"Smart Charging","flow.solar":"Solar","flow.grid":"Grid","flow.export":"Export","flow.battery":"Battery","flow.home":"Home","flow.car":"Car","flow.no_car":"No car","control.mode":"Mode","control.battery":"Battery","control.manual_charge":"Charge now","control.manual_current":"Current","control.manual_phases":"Phases","control.smart_control":"Smart control","control.auto_phase":"Auto phase (1\u21943)","control.battery_fill_to":"Fill battery to","control.battery_use_to":"Use battery down to","control.target_energy":"Car target energy","control.tag":"Tag","action.start":"Start","action.stop":"Stop","reason.smart_disabled":"Smart control disabled","reason.mode_off":"Mode: Off \u2014 manual control","reason.manual_paused":"Manual mode \u2014 paused","reason.manual_charging":"Manual charging at {amps} A","reason.manual_charging_guarded":"Manual charging at {amps} A (protecting home battery)","reason.no_car":"No car connected","reason.fast":"Fast charging at {amps} A","reason.cheap_grid":"Cheap grid {price}/kWh \u2264 {threshold} \u2192 full power","reason.cheap_grid_guarded":"Cheap grid {price}/kWh \u2264 {threshold} \u2192 full power (protecting home battery \u2192 {amps} A)","reason.deadline_plan":"Cheap-hours plan: charging now at {price}/kWh to reach {target} kWh by departure","reason.deadline_plan_guarded":"Cheap-hours plan: charging now at {price}/kWh to reach {target} kWh by departure (protecting home battery \u2192 {amps} A)","reason.holding_off_dwell":"Holding off (anti-flap dwell)","reason.price_waiting":"Waiting for a cheaper price window","reason.charging":"Charging","reason.waiting_battery_reserve":"Waiting \u2014 home battery {soc}% < reserve {reserve}%","reason.waiting_surplus":"Waiting for surplus \u2014 {surplus} W < {needed} W needed","reason.solar_surplus":"Solar surplus {surplus} W \u2192 {amps} A","reason.solar_surplus_phase":"Solar surplus {surplus} W \u2192 {amps} A ({phases}-phase)","reason.solar_min_topup":"Minimum {amps} A (surplus only {surplus} W, topping up from grid)","reason.holding_charge_dwell":"Holding charge (anti-flap dwell)","session.none":"No active session","session.charging":"Charging: {state}","session.last":"Last session: {energy}","session.blocked":"blocked","session.tag":"tag","editor.device":"Smart Charging device (optional \u2014 auto-detected)","editor.title":"Title (optional)","editor.show_flow":"Show energy flow","editor.show_controls":"Show controls","editor.show_sessions":"Show sessions & RFID","editor.hours":"Hours to show (optional)","price.title":"Electricity price","price.no_price":"No price forecast available. Configure a price sensor for {name} first.","price.cheap_threshold":"Cheap below","price.cheap_hours":"{hours} cheap upcoming","price.next_window":"next {start}\u2013{end}","price.no_cheap":"No cheap hours coming up at this threshold","price.now":"now","price.tomorrow":"Tomorrow"},de={"card.no_device":"Kein {name}-Ger\xE4t gefunden. Richte zuerst eines ein und f\xFCge dann diese Karte hinzu.","card.default_title":"Intelligentes Laden","flow.solar":"Solar","flow.grid":"Netz","flow.export":"Einspeisung","flow.battery":"Batterie","flow.home":"Haus","flow.car":"Auto","flow.no_car":"Kein Auto","control.mode":"Modus","control.battery":"Batterie","control.manual_charge":"Jetzt laden","control.manual_current":"Stromst\xE4rke","control.manual_phases":"Phasen","control.smart_control":"Intelligente Steuerung","control.auto_phase":"Auto-Phase (1\u21943)","control.battery_fill_to":"Batterie laden bis","control.battery_use_to":"Batterie nutzen bis","control.target_energy":"Ziel-Energie Auto","control.tag":"Tag","action.start":"Starten","action.stop":"Stoppen","reason.smart_disabled":"Intelligente Steuerung deaktiviert","reason.mode_off":"Modus: Aus \u2014 manuelle Steuerung","reason.manual_paused":"Manueller Modus \u2014 pausiert","reason.manual_charging":"Manuelles Laden mit {amps} A","reason.manual_charging_guarded":"Manuelles Laden mit {amps} A (Hausbatterie gesch\xFCtzt)","reason.no_car":"Kein Auto verbunden","reason.fast":"Schnellladen mit {amps} A","reason.cheap_grid":"G\xFCnstiger Netzstrom {price}/kWh \u2264 {threshold} \u2192 volle Leistung","reason.cheap_grid_guarded":"G\xFCnstiger Netzstrom {price}/kWh \u2264 {threshold} \u2192 volle Leistung (Hausbatterie gesch\xFCtzt \u2192 {amps} A)","reason.deadline_plan":"G\xFCnstig-Stunden-Plan: l\xE4dt jetzt zu {price}/kWh, um {target} kWh bis zur Abfahrt zu erreichen","reason.deadline_plan_guarded":"G\xFCnstig-Stunden-Plan: l\xE4dt jetzt zu {price}/kWh, um {target} kWh bis zur Abfahrt zu erreichen (Hausbatterie gesch\xFCtzt \u2192 {amps} A)","reason.holding_off_dwell":"Pausiert (Anti-Flatter-Sperre)","reason.price_waiting":"Warten auf ein g\xFCnstigeres Preisfenster","reason.charging":"L\xE4dt","reason.waiting_battery_reserve":"Warten \u2014 Hausbatterie {soc}% < Reserve {reserve}%","reason.waiting_surplus":"Warten auf \xDCberschuss \u2014 {surplus} W < {needed} W ben\xF6tigt","reason.solar_surplus":"Solar\xFCberschuss {surplus} W \u2192 {amps} A","reason.solar_surplus_phase":"Solar\xFCberschuss {surplus} W \u2192 {amps} A ({phases}-phasig)","reason.solar_min_topup":"Minimum {amps} A (nur {surplus} W \xDCberschuss, Aufstockung aus dem Netz)","reason.holding_charge_dwell":"Ladung gehalten (Anti-Flatter-Sperre)","session.none":"Kein aktiver Ladevorgang","session.charging":"L\xE4dt: {state}","session.last":"Letzter Ladevorgang: {energy}","session.blocked":"gesperrt","session.tag":"Tag","editor.device":"Smart-Charging-Ger\xE4t (optional \u2014 automatisch erkannt)","editor.title":"Titel (optional)","editor.show_flow":"Energiefluss anzeigen","editor.show_controls":"Steuerung anzeigen","editor.show_sessions":"Ladevorg\xE4nge & RFID anzeigen","editor.hours":"Anzuzeigende Stunden (optional)","price.title":"Strompreis","price.no_price":"Keine Preisprognose verf\xFCgbar. Richte zuerst einen Preissensor f\xFCr {name} ein.","price.cheap_threshold":"G\xFCnstig unter","price.cheap_hours":"{hours} g\xFCnstig in K\xFCrze","price.next_window":"n\xE4chste {start}\u2013{end}","price.no_cheap":"Bei dieser Schwelle keine g\xFCnstigen Stunden in Sicht","price.now":"jetzt","price.tomorrow":"Morgen"},pe={en:Et,de};function ue(o){let t=(o?.locale?.language||o?.language||"en").toLowerCase().split("-")[0];return pe[t]??Et}function $(o,t,e={}){let r=ue(o)[t]??Et[t]??t;for(let[i,n]of Object.entries(e))r=r.replace(`{${i}}`,n);return r}var D=class extends b{constructor(){super(...arguments);this._schema=[{name:"device",selector:{device:{integration:R}}},{name:"title",selector:{text:{}}},{type:"grid",name:"",schema:[{name:"show_flow",selector:{boolean:{}}},{name:"show_controls",selector:{boolean:{}}},{name:"show_sessions",selector:{boolean:{}}}]}];this._label=e=>{switch(e.name){case"device":return $(this.hass,"editor.device");case"title":return $(this.hass,"editor.title");case"show_flow":return $(this.hass,"editor.show_flow");case"show_controls":return $(this.hass,"editor.show_controls");case"show_sessions":return $(this.hass,"editor.show_sessions");default:return e.name}}}setConfig(e){this._config=e}render(){return!this.hass||!this._config?l:d`<ha-form
      .hass=${this.hass}
      .data=${this._config}
      .schema=${this._schema}
      .computeLabel=${this._label}
      @value-changed=${this._valueChanged}
    ></ha-form>`}_valueChanged(e){let s={...e.detail.value};this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:s},bubbles:!0,composed:!0}))}};D.styles=E`
    ha-form {
      display: block;
      padding: 8px 0;
    }
  `,y([x({attribute:!1})],D.prototype,"hass",2),y([N()],D.prototype,"_config",2),D=y([H("goe-steve-card-editor")],D);var W=class extends b{constructor(){super(...arguments);this._schema=[{name:"device",selector:{device:{integration:R}}},{name:"title",selector:{text:{}}},{name:"hours",selector:{number:{min:6,max:48,mode:"box",unit_of_measurement:"h"}}}];this._label=e=>{switch(e.name){case"device":return $(this.hass,"editor.device");case"title":return $(this.hass,"editor.title");case"hours":return $(this.hass,"editor.hours");default:return e.name}}}setConfig(e){this._config=e}render(){return!this.hass||!this._config?l:d`<ha-form
      .hass=${this.hass}
      .data=${this._config}
      .schema=${this._schema}
      .computeLabel=${this._label}
      @value-changed=${this._valueChanged}
    ></ha-form>`}_valueChanged(e){let s={...e.detail.value};this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:s},bubbles:!0,composed:!0}))}};W.styles=E`
    ha-form {
      display: block;
      padding: 8px 0;
    }
  `,y([x({attribute:!1})],W.prototype,"hass",2),y([N()],W.prototype,"_config",2),W=y([H("goe-steve-price-card-editor")],W);var ge="go-e + SteVe Smart Charging",q=480,ut=200,f={left:38,right:10,top:12,bottom:24},me=q-f.left-f.right,Ct=ut-f.top-f.bottom,pt=36e5,P=class extends b{constructor(){super(...arguments);this._dragValue=null;this._dragging=!1;this._cheapCache=null}static getConfigElement(){return document.createElement("goe-steve-price-card-editor")}static getStubConfig(e){return{type:"custom:goe-steve-price-card",device:st(e)[0]?.id}}setConfig(e){this._config={...e}}getCardSize(){return 6}get _entities(){return this.hass?dt(this.hass,this._config?.device):null}_t(e,s={}){return $(this.hass,e,s)}_stateObj(e){return e?this.hass.states[e]:void 0}_deviceName(e){if(!e)return null;let s=this.hass.devices[e];return s?.name_by_user||s?.name||null}_slots(e){let r=(e.attributes.slots??[]).map(i=>({start:Date.parse(i.start??""),price:Number(i.price)})).filter(i=>!Number.isNaN(i.start)&&!Number.isNaN(i.price)).sort((i,n)=>i.start-n.start);return r.map((i,n)=>({start:i.start,end:n+1<r.length?r[n+1].start:i.start+pt,price:i.price}))}_cheap(e,s){let r=this._stateObj(e.cheap_price),i=Number(s.attributes.cheap_price),n=r?Number(r.state):Number.isNaN(i)?.15:i,a=r?.attributes??{};return{obj:r,value:n,min:Number(a.min??0),max:Number(a.max??1),step:Number(a.step??.01),unit:s.attributes.unit??a.unit_of_measurement??""}}render(){if(!this.hass||!this._config)return l;let e=this._entities,s=this._stateObj(e?.price_forecast),r=s?this._slots(s):[],i=this._config.title??this._deviceName(e?.deviceId)??this._t("price.title");if(!s||r.length===0){let[c,p]=this._t("price.no_price").split("{name}");return d`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:cash-clock"></ha-icon>
          <p>${c}<b>${ge}</b>${p??""}</p>
        </div>
      </ha-card>`}let n=this._cheap(e,s),a=this._dragValue??n.value;return d`<ha-card>
      <div class="header">
        <div class="title-row">
          <ha-icon icon="mdi:cash-clock"></ha-icon>
          <span class="title">${i}</span>
        </div>
        <div class="now-price">${this._fmtPrice(Number(s.state),n.unit)}</div>
      </div>
      ${this._renderChart(r,a)}
      ${this._renderPreview(r,a)}
      ${this._renderThresholdInput(n,a)}
    </ha-card>`}_shownSlots(e){let s=Date.now(),r=e.filter(i=>i.end>s);if(r.length===0&&(r=e.slice(-1)),this._config.hours&&this._config.hours>0){let i=s+this._config.hours*pt;r=r.filter(n=>n.start<i)}return r.slice(0,96)}_renderChart(e,s){let r=Date.now(),i=this._shownSlots(e),n=i[0].start,a=i[i.length-1].end,c=i.map(v=>v.price),p=Math.min(...c,s),u=Math.max(...c,s),h=u-p||1,g=p-h*.1,_=u+h*.1,m=v=>f.left+(v-n)/(a-n)*me,w=v=>f.top+(1-(v-g)/(_-g))*Ct,M=f.top+Ct,A=w(s),V=i.map(v=>{let S=m(v.start),z=m(v.end),Nt=w(v.price),Kt=v.price<=s;return k`<rect
        class="bar ${Kt?"cheap":""}"
        x=${S+.5}
        y=${Nt}
        width=${Math.max(.5,z-S-1)}
        height=${Math.max(0,M-Nt)}
      ></rect>`}),K=[];for(let v of i){let S=new Date(v.start);if(S.getHours()===0&&S.getMinutes()===0&&v.start>n){let z=m(v.start);K.push(k`<line class="day-div" x1=${z} y1=${f.top} x2=${z} y2=${M}></line>`),K.push(k`<text class="day-lbl" x=${z+3} y=${f.top+9}>${this._t("price.tomorrow")}</text>`)}}let kt=[];for(let v of i){let S=new Date(v.start);if(S.getHours()%6===0&&S.getMinutes()===0){let z=m(v.start);kt.push(k`<text class="x-tick" x=${z} y=${ut-8}>${String(S.getHours()).padStart(2,"0")}</text>`)}}let it=r>=n&&r<=a?m(r):null;return d`<div class="chart">
      <svg
        viewBox="0 0 ${q} ${ut}"
        preserveAspectRatio="none"
        @pointermove=${this._onPointerMove}
        @pointerup=${this._onPointerUp}
        @pointercancel=${this._onPointerUp}
      >
        <!-- y grid: min / threshold / max -->
        <text class="y-tick" x=${f.left-4} y=${w(_)+3}>${this._fmtNum(u)}</text>
        <text class="y-tick" x=${f.left-4} y=${M}>${this._fmtNum(p)}</text>
        ${K}
        ${V}
        ${kt}
        ${it!==null?k`<line class="now-line" x1=${it} y1=${f.top} x2=${it} y2=${M}></line>
                 <text class="now-tick" x=${it} y=${f.top-2}>${this._t("price.now")}</text>`:l}
        <!-- threshold line + draggable handle -->
        <line class="thresh" x1=${f.left} y1=${A} x2=${q-f.right} y2=${A}></line>
        <g class="handle" data-handle @pointerdown=${this._onPointerDown}>
          <!-- generous, invisible touch target so fingers can grab the handle -->
          <rect class="handle-hit" x=${q-f.right-68} y=${A-20} width="72" height="40"></rect>
          <rect class="handle-chip" x=${q-f.right-52} y=${A-9} width="52" height="18" rx="4"></rect>
          <text x=${q-f.right-26} y=${A+4}>${this._fmtNum(s)}</text>
        </g>
      </svg>
    </div>`}_onPointerDown(e){let s=this._entities,r=this._stateObj(s?.price_forecast);!s||!r||!s.cheap_price||(this._cheapCache=this._cheap(s,r),this._dragging=!0,e.target.setPointerCapture?.(e.pointerId),e.preventDefault(),this._updateDrag(e))}_onPointerMove(e){this._dragging&&(e.preventDefault(),this._updateDrag(e))}_onPointerUp(){if(!this._dragging)return;this._dragging=!1;let e=this._cheapCache,s=this._dragValue;this._dragValue=null,this._cheapCache=null,e?.obj&&s!==null&&s!==e.value&&this.hass.callService("number","set_value",{entity_id:e.obj.entity_id,value:s})}_updateDrag(e){let s=this._cheapCache;if(!s)return;let r=this.renderRoot.querySelector("svg");if(!r)return;let i=r.getBoundingClientRect(),n=(e.clientY-i.top)/i.height*ut,{yMin:a,yMax:c}=this._yDomain(s),p=1-(n-f.top)/Ct,u=a+p*(c-a);u=Math.min(s.max,Math.max(s.min,u)),s.step>0&&(u=Math.round(u/s.step)*s.step);let h=(String(s.step).split(".")[1]??"").length||2;this._dragValue=Number(u.toFixed(h))}_yDomain(e){let s=this._entities,r=this._stateObj(s?.price_forecast),i=r?this._slots(r):[],n=this._shownSlots(i),a=this._dragValue??e.value,c=n.map(g=>g.price),p=Math.min(...c,a),u=Math.max(...c,a),h=u-p||1;return{yMin:p-h*.1,yMax:u+h*.1}}_renderPreview(e,s){let r=Date.now(),n=e.filter(h=>h.end>r).filter(h=>h.price<=s);if(n.length===0)return d`<div class="preview muted">
        <ha-icon icon="mdi:flash-off"></ha-icon><span>${this._t("price.no_cheap")}</span>
      </div>`;let a=n.reduce((h,g)=>h+(Math.min(g.end,r+48*pt)-Math.max(g.start,r))/pt,0),c=n[0],p=c.end;for(let h=1;h<n.length&&n[h].start===p;h++)p=n[h].end;let u=`${a.toFixed(a<10?1:0)} h`;return d`<div class="preview">
      <ha-icon icon="mdi:flash"></ha-icon>
      <span>${this._t("price.cheap_hours",{hours:u})}</span>
      <span class="sep">·</span>
      <span class="muted"
        >${this._t("price.next_window",{start:this._fmtTime(Math.max(c.start,r)),end:this._fmtTime(p)})}</span
      >
    </div>`}_renderThresholdInput(e,s){return e.obj?d`<div class="threshold-row">
      <span class="thr-label">${this._t("price.cheap_threshold")}</span>
      <span class="thr-input">
        <input
          type="number"
          .value=${String(s)}
          min=${e.min}
          max=${e.max}
          step=${e.step}
          @change=${r=>this._setThreshold(e,r.target.value)}
        />
        ${e.unit?d`<span class="thr-unit">${e.unit}</span>`:l}
      </span>
    </div>`:l}_setThreshold(e,s){let r=Number(s);!e.obj||Number.isNaN(r)||r===e.value||this.hass.callService("number","set_value",{entity_id:e.obj.entity_id,value:r})}_fmtNum(e){return e.toFixed(Math.abs(e)<1?2:1)}_fmtPrice(e,s){return Number.isNaN(e)?"\u2014":`${this._fmtNum(e)}${s?` ${s}`:""}`}_fmtTime(e){return new Date(e).toLocaleTimeString(this.hass?.locale?.language??[],{hour:"2-digit",minute:"2-digit"})}};P.styles=E`
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

    /* Chart */
    .chart {
      padding: 0 8px;
    }
    .chart svg {
      width: 100%;
      height: 200px;
      /* default touch-action: vertical swipes scroll the page normally;
         only the handle (below) owns the drag gesture. */
    }
    .bar {
      fill: var(--divider-color);
    }
    .bar.cheap {
      fill: var(--primary-color);
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
      stroke: var(--error-color, #db4437);
      stroke-width: 1.5;
    }
    .now-tick {
      fill: var(--error-color, #db4437);
      font-size: 9px;
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
  `,y([x({attribute:!1})],P.prototype,"hass",2),y([N()],P.prototype,"_config",2),y([N()],P.prototype,"_dragValue",2),P=y([H("goe-steve-price-card")],P);window.customCards=window.customCards||[];window.customCards.push({type:"goe-steve-price-card",name:"go-e + SteVe Price",description:"Electricity-price forecast with a draggable 'cheap' threshold \u2014 see the curve and set what counts as cheap.",preview:!0,documentationURL:"https://github.com/JustChr/HAgoe_steve"});var _e="go-e + SteVe Smart Charging",rt=o=>{if(o==null||Number.isNaN(o))return"\u2014";let t=Math.abs(o);return t>=1e3?`${(o/1e3).toFixed(t>=1e4?0:1)} kW`:`${Math.round(o)} W`},I=class extends b{static getConfigElement(){return document.createElement("goe-steve-card-editor")}static getStubConfig(t){return{type:"custom:goe-steve-card",device:st(t)[0]?.id}}setConfig(t){this._config={show_flow:!0,show_controls:!0,show_sessions:!0,...t}}getCardSize(){return 8}get _entities(){return this.hass?dt(this.hass,this._config?.device):null}_t(t,e={}){return $(this.hass,t,e)}render(){if(!this.hass||!this._config)return l;let t=this._entities;if(!t||!t.deviceId)return d`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:ev-station"></ha-icon>
          <p>${this._renderNoDevice()}</p>
        </div>
      </ha-card>`;let e=this._config.title??this._deviceName(t.deviceId)??this._t("card.default_title");return d`<ha-card>
      ${this._renderHeader(t,e)}
      <div class="content">
        ${this._config.show_flow?this._renderFlow(t):l}
        ${this._config.show_controls?this._renderControls(t):l}
        ${this._config.show_sessions?this._renderSessions(t):l}
      </div>
    </ha-card>`}_renderNoDevice(){let[t,e]=this._t("card.no_device").split("{name}");return d`${t}<b>${_e}</b>${e??""}`}_renderHeader(t,e){let s=this._stateObj(t.status),r=this._statusReason(s),i=this._isOn(t.controlling),n=this._displayState(t.charging_mode),a=this._displayState(t.battery_policy);return d`<div class="header">
      <div class="title-row">
        <ha-icon class="brain ${i?"active":""}" icon="mdi:brain"></ha-icon>
        <span class="title">${e}</span>
      </div>
      <div class="reason">${r}</div>
      <div class="chips">
        ${n?d`<span class="chip"><ha-icon icon="mdi:ev-station"></ha-icon>${n}</span>`:l}
        ${a?d`<span class="chip"><ha-icon icon="mdi:home-battery"></ha-icon>${a}</span>`:l}
      </div>
    </div>`}_statusReason(t){let e=t?.state&&t.state!=="unknown"?t.state:"\u2014",s=t?.attributes?.reason_key;if(!s)return e;let r=`reason.${s}`,i=t?.attributes?.reason_params??{},n=this._t(r,this._localizeNumbers(i));return n===r?e:n}_localizeNumbers(t){let e=(this.hass?.locale?.language||this.hass?.language||"en").toLowerCase().split("-")[0],s={};for(let[r,i]of Object.entries(t)){let n=/^-?\d+(?:\.(\d+))?$/.exec(i);if(n){let a=n[1]?.length??0;s[r]=new Intl.NumberFormat(e,{minimumFractionDigits:a,maximumFractionDigits:a}).format(Number(i))}else s[r]=i}return s}_renderFlow(t){let e=this._stateObj(t.power_flow),s=e?.attributes??{},r=Number(s.pv_w??NaN),i=Number(s.grid_w??NaN),n=s.battery_w===null||s.battery_w===void 0?null:Number(s.battery_w),a=Number(s.car_w??(e?e.state:NaN)),c=Number(s.house_w??NaN),p=s.battery_soc,u=s.car_connected,h=50,g=(m,w,M,A,V,K="")=>k`
      <g class="node" transform="translate(${m},${w})">
        <circle r="26"></circle>
        <foreignObject x="-13" y="-20" width="26" height="26">
          <ha-icon icon="${M}"></ha-icon>
        </foreignObject>
        <text class="node-val" y="14">${V}</text>
        <text class="node-lbl" y="42">${A}${K}</text>
      </g>`,_=(m,w,M,A)=>{let V=w?Math.max(.6,3-Math.min(A,9e3)/3e3):0;return k`
        <path class="edge" d="${m}"></path>
        <path
          class="edge-flow ${w?"active":""} ${M?"rev":""}"
          d="${m}"
          style="${w?`animation-duration:${V}s`:""}"
        ></path>`};return d`<div class="flow">
      <svg viewBox="0 0 320 336" preserveAspectRatio="xMidYMid meet">
        ${_("M160,66 L160,134",r>h,!1,r)}
        ${_("M76,160 L134,160",Number.isNaN(i)?!1:Math.abs(i)>h,i<0,Math.abs(i))}
        ${n!==null?_("M244,160 L186,160",Math.abs(n)>h,n>0,Math.abs(n)):l}
        ${_("M160,186 L160,244",a>h,!1,a)}

        ${g(160,40,"mdi:solar-power",this._t("flow.solar"),rt(r))}
        ${g(40,160,"mdi:transmission-tower",i<0?this._t("flow.export"):this._t("flow.grid"),rt(Math.abs(i)))}
        ${n!==null?g(280,160,"mdi:home-battery",this._t("flow.battery"),rt(Math.abs(n)),p!=null?` ${Math.round(Number(p))}%`:""):l}
        ${g(160,160,"mdi:home",this._t("flow.home"),rt(c))}
        ${g(160,280,u===!1?"mdi:car-off":"mdi:car-electric",u===!1?this._t("flow.no_car"):this._t("flow.car"),rt(a))}
      </svg>
    </div>`}_renderControls(t){let e=this._stateObj(t.charging_mode),s=this._stateObj(t.battery_policy),r=this._stateObj(t.smart_control),i=this._stateObj(t.battery_reserve_soc),n=this._stateObj(t.battery_floor_soc),a=this._stateObj(t.target_energy),c=s?.state,p=e?.state,u=p==="off",h=this._stateObj(t.manual_charge),g=this._stateObj(t.manual_current),_=this._stateObj(t.manual_phases);return d`<div class="controls">
      ${e?d`<div class="control">
            <span class="ctl-label">${this._t("control.mode")}</span>
            ${this._renderSelect(e)}
          </div>`:l}
      ${u&&h?d`<div class="control">
            <span class="ctl-label">${this._t("control.manual_charge")}</span>
            <ha-switch
              .checked=${this._isOn(t.manual_charge)}
              @change=${m=>this._toggle(t.manual_charge,m)}
            ></ha-switch>
          </div>`:l}
      ${u&&g?d`<div class="control">
            <span class="ctl-label">${this._t("control.manual_current")}</span>
            ${this._renderNumber(g)}
          </div>`:l}
      ${u&&_?d`<div class="control">
            <span class="ctl-label">${this._t("control.manual_phases")}</span>
            ${this._renderSelect(_)}
          </div>`:l}
      ${s?d`<div class="control">
            <span class="ctl-label">${this._t("control.battery")}</span>
            ${this._renderSelect(s)}
          </div>`:l}
      ${i&&c==="protect"?d`<div class="control">
            <span class="ctl-label">${this._t("control.battery_fill_to")}</span>
            ${this._renderNumber(i)}
          </div>`:l}
      ${i&&c==="share"?d`<div class="control">
            <span class="ctl-label">${this._t("control.battery_use_to")}</span>
            ${this._renderNumber(i)}
          </div>`:l}
      ${n&&c==="assist"?d`<div class="control">
            <span class="ctl-label">${this._t("control.battery_use_to")}</span>
            ${this._renderNumber(n)}
          </div>`:l}
      ${a&&(p==="price"||p==="combined")?d`<div class="control">
            <span class="ctl-label">${this._t("control.target_energy")}</span>
            ${this._renderNumber(a)}
          </div>`:l}
      ${r?d`<div class="control">
            <span class="ctl-label">${this._t("control.smart_control")}</span>
            <ha-switch
              .checked=${this._isOn(t.smart_control)}
              @change=${m=>this._toggle(t.smart_control,m)}
            ></ha-switch>
          </div>`:l}
      ${t.auto_phase&&!u?d`<div class="control">
            <span class="ctl-label">${this._t("control.auto_phase")}</span>
            <ha-switch
              .checked=${this._isOn(t.auto_phase)}
              @change=${m=>this._toggle(t.auto_phase,m)}
            ></ha-switch>
          </div>`:l}
    </div>`}_renderNumber(t){let e=t.attributes,s=e.unit_of_measurement??"";return d`<span class="ctl-number-wrap">
      <input
        class="ctl-number"
        type="number"
        .value=${t.state}
        min=${e.min??l}
        max=${e.max??l}
        step=${e.step??l}
        @change=${r=>this._setNumber(t,r.target.value)}
      />
      ${s?d`<span class="ctl-unit">${s}</span>`:l}
    </span>`}_setNumber(t,e){let s=Number(e);Number.isNaN(s)||String(s)===t.state||this.hass.callService("number","set_value",{entity_id:t.entity_id,value:s})}_renderSelect(t){let e=t.attributes.options??[];return d`<select
      class="ctl-select"
      @change=${s=>this._selectOption(t,s.target.value)}
    >
      ${e.map(s=>d`<option .value=${s} ?selected=${s===t.state}>
            ${this._localizeOption(t,s)}
          </option>`)}
    </select>`}_renderSessions(t){let e=this._stateObj(t.active_transaction),s=this._stateObj(t.last_session_energy),r=this._stateObj(t.selected_tag),i=t.tag_energy.map(a=>this._stateObj(a)).filter(a=>!!a);if(!e&&!s&&!r&&i.length===0)return l;let n=!!e&&!["idle","unknown","unavailable",""].includes(e.state);return d`<div class="sessions">
      ${this._renderTagPicker(r,n)}
      ${e?d`<div class="session-row">
            <ha-icon icon="mdi:card-account-details"></ha-icon>
            <span>${e.state==="idle"?this._t("session.none"):this._t("session.charging",{state:e.attributes.name??e.state})}</span>
          </div>`:l}
      ${s&&s.state&&s.state!=="unknown"?d`<div class="session-row">
            <ha-icon icon="mdi:history"></ha-icon>
            <span>${this._t("session.last",{energy:this._fmtState(s)})}</span>
          </div>`:l}
      ${i.length?d`<div class="tags">
            ${i.map(a=>d`<div class="tag">
                <span class="tag-id">${a.attributes.name??a.attributes.id_tag??this._t("session.tag")}</span>
                <span class="tag-kwh ${a.attributes.blocked?"blocked":""}">
                  ${this._fmtState(a)}${a.attributes.blocked?` \xB7 ${this._t("session.blocked")}`:""}
                </span>
              </div>`)}
          </div>`:l}
    </div>`}_renderTagPicker(t,e){if(!t)return l;let s=t.attributes.options??[];if(s.length===0)return l;let r=s.includes(t.state);return d`<div class="tag-picker">
      ${e?l:d`<div class="control">
            <span class="ctl-label">${this._t("control.tag")}</span>
            ${this._renderSelect(t)}
          </div>`}
      <div class="tag-actions">
        ${e?d`<button
              class="tag-btn stop"
              @click=${()=>this._callTagService("remote_stop")}
            >
              <ha-icon icon="mdi:stop"></ha-icon>${this._t("action.stop")}
            </button>`:d`<button
                class="tag-btn"
                ?disabled=${!r}
                @click=${()=>this._callTagService("remote_start")}
              >
                <ha-icon icon="mdi:play"></ha-icon>${this._t("action.start")}
              </button>`}
      </div>
    </div>`}_callTagService(t){this.hass.callService(R,t,{})}_stateObj(t){return t?this.hass.states[t]:void 0}_isOn(t){return this._stateObj(t)?.state==="on"}_displayState(t){let e=this._stateObj(t);return e?this._fmtState(e):null}_fmtState(t){return this.hass.formatEntityState?this.hass.formatEntityState(t):t.state}_localizeOption(t,e){let s=this.hass.entities?.[t.entity_id]?.translation_key;if(s){let r=`component.${R}.entity.select.${s}.state.${e}`,i=this.hass.localize?.(r);if(i)return i}if(this.hass.formatEntityState){let r=this.hass.formatEntityState({...t,state:e},e);if(r)return r}return e}_deviceName(t){let e=this.hass.devices[t];return e?.name_by_user||e?.name||null}_selectOption(t,e){e!==t.state&&this.hass.callService("select","select_option",{entity_id:t.entity_id,option:e})}_toggle(t,e){if(!t)return;let s=e.target.checked;this.hass.callService("switch",s?"turn_on":"turn_off",{entity_id:t})}};I.styles=E`
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
    .header {
      padding: 16px 16px 8px;
    }
    .title-row {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .title {
      font-size: 1.25rem;
      font-weight: 500;
    }
    .brain {
      color: var(--disabled-text-color);
      transition: color 0.3s ease;
    }
    .brain.active {
      color: var(--primary-color);
    }
    .reason {
      margin-top: 4px;
      color: var(--secondary-text-color);
      font-size: 0.95rem;
      min-height: 1.2em;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 10px;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 10px;
      border-radius: 14px;
      background: var(--secondary-background-color);
      font-size: 0.8rem;
      color: var(--primary-text-color);
    }
    .chip ha-icon {
      --mdc-icon-size: 15px;
      color: var(--primary-color);
    }
    .content {
      padding: 0 8px 8px;
    }

    /* Flow diagram */
    .flow svg {
      width: 100%;
      height: auto;
      max-height: 336px;
    }
    .node circle {
      fill: var(--card-background-color);
      stroke: var(--divider-color);
      stroke-width: 1.5;
    }
    .node ha-icon {
      --mdc-icon-size: 22px;
      color: var(--primary-color);
    }
    .node-val {
      text-anchor: middle;
      font-size: 11px;
      font-weight: 600;
      fill: var(--primary-text-color);
    }
    .node-lbl {
      text-anchor: middle;
      font-size: 10px;
      fill: var(--secondary-text-color);
    }
    .edge {
      fill: none;
      stroke: var(--divider-color);
      stroke-width: 2;
    }
    .edge-flow {
      fill: none;
      stroke: var(--primary-color);
      stroke-width: 3;
      stroke-linecap: round;
      stroke-dasharray: 4 10;
      opacity: 0;
    }
    .edge-flow.active {
      opacity: 0.9;
      animation-name: dash;
      animation-timing-function: linear;
      animation-iteration-count: infinite;
    }
    .edge-flow.active.rev {
      animation-name: dash-rev;
    }
    @keyframes dash {
      to {
        stroke-dashoffset: -14;
      }
    }
    @keyframes dash-rev {
      to {
        stroke-dashoffset: 14;
      }
    }

    /* Controls */
    .controls {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 4px 8px 8px;
    }
    .control {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }
    .ctl-label {
      color: var(--secondary-text-color);
      font-size: 0.9rem;
      white-space: nowrap;
    }
    .ctl-select {
      min-width: 180px;
      flex: 1;
      max-width: 60%;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--ha-card-background));
      color: var(--primary-text-color);
      font-family: inherit;
      font-size: 0.95rem;
      cursor: pointer;
    }
    .ctl-select:focus {
      outline: none;
      border-color: var(--primary-color);
    }
    .ctl-number-wrap {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      flex: 1;
      max-width: 60%;
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
      font-size: 0.95rem;
      text-align: right;
    }
    .ctl-number:focus {
      outline: none;
      border-color: var(--primary-color);
    }
    .ctl-unit {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
      white-space: nowrap;
    }

    /* Sessions */
    .sessions {
      border-top: 1px solid var(--divider-color);
      margin: 4px 8px 0;
      padding-top: 8px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .session-row {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.9rem;
      color: var(--primary-text-color);
    }
    .session-row ha-icon {
      --mdc-icon-size: 18px;
      color: var(--secondary-text-color);
    }
    .tags {
      display: flex;
      flex-direction: column;
      gap: 4px;
      margin-top: 2px;
    }
    .tag {
      display: flex;
      justify-content: space-between;
      font-size: 0.85rem;
      padding: 2px 0;
    }
    .tag-picker {
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding-bottom: 4px;
    }
    .tag-actions {
      display: flex;
      gap: 8px;
    }
    .tag-btn {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      flex: 1;
      justify-content: center;
      padding: 8px 10px;
      border-radius: 8px;
      border: 1px solid var(--divider-color);
      background: var(--card-background-color, var(--ha-card-background));
      color: var(--primary-text-color);
      font-family: inherit;
      font-size: 0.9rem;
      cursor: pointer;
    }
    .tag-btn ha-icon {
      --mdc-icon-size: 18px;
      color: var(--primary-color);
    }
    .tag-btn:hover:not([disabled]) {
      border-color: var(--primary-color);
    }
    .tag-btn[disabled] {
      opacity: 0.5;
      cursor: default;
    }
    .tag-btn.stop {
      color: var(--error-color, #db4437);
    }
    .tag-btn.stop ha-icon {
      color: var(--error-color, #db4437);
    }
    .tag-btn.stop:hover:not([disabled]) {
      border-color: var(--error-color, #db4437);
    }
    .tag-id {
      color: var(--secondary-text-color);
    }
    .tag-kwh {
      font-weight: 600;
    }
    .tag-kwh.blocked {
      color: var(--error-color, #db4437);
      font-weight: 500;
    }
  `,y([x({attribute:!1})],I.prototype,"hass",2),y([N()],I.prototype,"_config",2),I=y([H("goe-steve-card")],I);window.customCards=window.customCards||[];window.customCards.push({type:"goe-steve-card",name:"go-e + SteVe Smart Charging",description:"Live energy flow, charging mode & battery policy with the brain's reasoning, inline controls and per-RFID energy.",preview:!0,documentationURL:"https://github.com/JustChr/HAgoe_steve"});export{I as GoeSteveCard};
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
*/
