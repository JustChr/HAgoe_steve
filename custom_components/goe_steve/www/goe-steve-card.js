/* go-e + SteVe Smart Charging card — bundled, do not edit by hand. Source in /card. */
var Jt=Object.defineProperty;var Yt=Object.getOwnPropertyDescriptor;var f=(n,t,e,s)=>{for(var i=s>1?void 0:s?Yt(t,e):t,r=n.length-1,o;r>=0;r--)(o=n[r])&&(i=(s?o(t,e,i):o(i))||i);return s&&i&&Jt(t,e,i),i};var nt=globalThis,ot=nt.ShadowRoot&&(nt.ShadyCSS===void 0||nt.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,gt=Symbol(),kt=new WeakMap,J=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==gt)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(ot&&t===void 0){let s=e!==void 0&&e.length===1;s&&(t=kt.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&kt.set(e,t))}return t}toString(){return this.cssText}},Tt=n=>new J(typeof n=="string"?n:n+"",void 0,gt),A=(n,...t)=>{let e=n.length===1?n[0]:t.reduce((s,i,r)=>s+(o=>{if(o._$cssResult$===!0)return o.cssText;if(typeof o=="number")return o;throw Error("Value passed to 'css' function must be a 'css' function result: "+o+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+n[r+1],n[0]);return new J(e,n,gt)},Mt=(n,t)=>{if(ot)n.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let s=document.createElement("style"),i=nt.litNonce;i!==void 0&&s.setAttribute("nonce",i),s.textContent=e.cssText,n.appendChild(s)}},mt=ot?n=>n:n=>n instanceof CSSStyleSheet?(t=>{let e="";for(let s of t.cssRules)e+=s.cssText;return Tt(e)})(n):n;var{is:Zt,defineProperty:Xt,getOwnPropertyDescriptor:Qt,getOwnPropertyNames:Gt,getOwnPropertySymbols:te,getPrototypeOf:ee}=Object,at=globalThis,Ht=at.trustedTypes,se=Ht?Ht.emptyScript:"",ie=at.reactiveElementPolyfillSupport,Y=(n,t)=>n,Z={toAttribute(n,t){switch(t){case Boolean:n=n?se:null;break;case Object:case Array:n=n==null?n:JSON.stringify(n)}return n},fromAttribute(n,t){let e=n;switch(t){case Boolean:e=n!==null;break;case Number:e=n===null?null:Number(n);break;case Object:case Array:try{e=JSON.parse(n)}catch{e=null}}return e}},ct=(n,t)=>!Zt(n,t),Pt={attribute:!0,type:String,converter:Z,reflect:!1,useDefault:!1,hasChanged:ct};Symbol.metadata??=Symbol("metadata"),at.litPropertyMetadata??=new WeakMap;var C=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=Pt){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let s=Symbol(),i=this.getPropertyDescriptor(t,s,e);i!==void 0&&Xt(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){let{get:i,set:r}=Qt(this.prototype,t)??{get(){return this[e]},set(o){this[e]=o}};return{get:i,set(o){let a=i?.call(this);r?.call(this,o),this.requestUpdate(t,a,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??Pt}static _$Ei(){if(this.hasOwnProperty(Y("elementProperties")))return;let t=ee(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(Y("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(Y("properties"))){let e=this.properties,s=[...Gt(e),...te(e)];for(let i of s)this.createProperty(i,e[i])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[s,i]of e)this.elementProperties.set(s,i)}this._$Eh=new Map;for(let[e,s]of this.elementProperties){let i=this._$Eu(e,s);i!==void 0&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let s=new Set(t.flat(1/0).reverse());for(let i of s)e.unshift(mt(i))}else t!==void 0&&e.push(mt(t));return e}static _$Eu(t,e){let s=e.attribute;return s===!1?void 0:typeof s=="string"?s:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return Mt(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){let s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(i!==void 0&&s.reflect===!0){let r=(s.converter?.toAttribute!==void 0?s.converter:Z).toAttribute(e,s.type);this._$Em=t,r==null?this.removeAttribute(i):this.setAttribute(i,r),this._$Em=null}}_$AK(t,e){let s=this.constructor,i=s._$Eh.get(t);if(i!==void 0&&this._$Em!==i){let r=s.getPropertyOptions(i),o=typeof r.converter=="function"?{fromAttribute:r.converter}:r.converter?.fromAttribute!==void 0?r.converter:Z;this._$Em=i;let a=o.fromAttribute(e,r.type);this[i]=a??this._$Ej?.get(i)??a,this._$Em=null}}requestUpdate(t,e,s,i=!1,r){if(t!==void 0){let o=this.constructor;if(i===!1&&(r=this[t]),s??=o.getPropertyOptions(t),!((s.hasChanged??ct)(r,e)||s.useDefault&&s.reflect&&r===this._$Ej?.get(t)&&!this.hasAttribute(o._$Eu(t,s))))return;this.C(t,e,s)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:i,wrapped:r},o){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,o??e??this[t]),r!==!0||o!==void 0)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),i===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[i,r]of this._$Ep)this[i]=r;this._$Ep=void 0}let s=this.constructor.elementProperties;if(s.size>0)for(let[i,r]of s){let{wrapped:o}=r,a=this[i];o!==!0||this._$AL.has(i)||a===void 0||this.C(i,void 0,r,a)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(s=>s.hostUpdate?.()),this.update(e)):this._$EM()}catch(s){throw t=!1,this._$EM(),s}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};C.elementStyles=[],C.shadowRootOptions={mode:"open"},C[Y("elementProperties")]=new Map,C[Y("finalized")]=new Map,ie?.({ReactiveElement:C}),(at.reactiveElementVersions??=[]).push("2.1.2");var xt=globalThis,Ot=n=>n,lt=xt.trustedTypes,zt=lt?lt.createPolicy("lit-html",{createHTML:n=>n}):void 0,Bt="$lit$",M=`lit$${Math.random().toFixed(9).slice(2)}$`,qt="?"+M,re=`<${qt}>`,j=document,Q=()=>j.createComment(""),G=n=>n===null||typeof n!="object"&&typeof n!="function",wt=Array.isArray,ne=n=>wt(n)||typeof n?.[Symbol.iterator]=="function",_t=`[ 	
\f\r]`,X=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,Lt=/-->/g,jt=/>/g,z=RegExp(`>|${_t}(?:([^\\s"'>=/]+)(${_t}*=${_t}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),Ut=/'/g,Dt=/"/g,Ft=/^(?:script|style|textarea|title)$/i,St=n=>(t,...e)=>({_$litType$:n,strings:t,values:e}),p=St(1),N=St(2),xe=St(3),U=Symbol.for("lit-noChange"),l=Symbol.for("lit-nothing"),It=new WeakMap,L=j.createTreeWalker(j,129);function Vt(n,t){if(!wt(n)||!n.hasOwnProperty("raw"))throw Error("invalid template strings array");return zt!==void 0?zt.createHTML(t):t}var oe=(n,t)=>{let e=n.length-1,s=[],i,r=t===2?"<svg>":t===3?"<math>":"",o=X;for(let a=0;a<e;a++){let c=n[a],d,u,h=-1,g=0;for(;g<c.length&&(o.lastIndex=g,u=o.exec(c),u!==null);)g=o.lastIndex,o===X?u[1]==="!--"?o=Lt:u[1]!==void 0?o=jt:u[2]!==void 0?(Ft.test(u[2])&&(i=RegExp("</"+u[2],"g")),o=z):u[3]!==void 0&&(o=z):o===z?u[0]===">"?(o=i??X,h=-1):u[1]===void 0?h=-2:(h=o.lastIndex-u[2].length,d=u[1],o=u[3]===void 0?z:u[3]==='"'?Dt:Ut):o===Dt||o===Ut?o=z:o===Lt||o===jt?o=X:(o=z,i=void 0);let v=o===z&&n[a+1].startsWith("/>")?" ":"";r+=o===X?c+re:h>=0?(s.push(d),c.slice(0,h)+Bt+c.slice(h)+M+v):c+M+(h===-2?a:v)}return[Vt(n,r+(n[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),s]},tt=class n{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let r=0,o=0,a=t.length-1,c=this.parts,[d,u]=oe(t,e);if(this.el=n.createElement(d,s),L.currentNode=this.el.content,e===2||e===3){let h=this.el.content.firstChild;h.replaceWith(...h.childNodes)}for(;(i=L.nextNode())!==null&&c.length<a;){if(i.nodeType===1){if(i.hasAttributes())for(let h of i.getAttributeNames())if(h.endsWith(Bt)){let g=u[o++],v=i.getAttribute(h).split(M),y=/([.?@])?(.*)/.exec(g);c.push({type:1,index:r,name:y[2],strings:v,ctor:y[1]==="."?vt:y[1]==="?"?yt:y[1]==="@"?bt:F}),i.removeAttribute(h)}else h.startsWith(M)&&(c.push({type:6,index:r}),i.removeAttribute(h));if(Ft.test(i.tagName)){let h=i.textContent.split(M),g=h.length-1;if(g>0){i.textContent=lt?lt.emptyScript:"";for(let v=0;v<g;v++)i.append(h[v],Q()),L.nextNode(),c.push({type:2,index:++r});i.append(h[g],Q())}}}else if(i.nodeType===8)if(i.data===qt)c.push({type:2,index:r});else{let h=-1;for(;(h=i.data.indexOf(M,h+1))!==-1;)c.push({type:7,index:r}),h+=M.length-1}r++}}static createElement(t,e){let s=j.createElement("template");return s.innerHTML=t,s}};function q(n,t,e=n,s){if(t===U)return t;let i=s!==void 0?e._$Co?.[s]:e._$Cl,r=G(t)?void 0:t._$litDirective$;return i?.constructor!==r&&(i?._$AO?.(!1),r===void 0?i=void 0:(i=new r(n),i._$AT(n,e,s)),s!==void 0?(e._$Co??=[])[s]=i:e._$Cl=i),i!==void 0&&(t=q(n,i._$AS(n,t.values),i,s)),t}var ft=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??j).importNode(e,!0);L.currentNode=i;let r=L.nextNode(),o=0,a=0,c=s[0];for(;c!==void 0;){if(o===c.index){let d;c.type===2?d=new et(r,r.nextSibling,this,t):c.type===1?d=new c.ctor(r,c.name,c.strings,this,t):c.type===6&&(d=new $t(r,this,t)),this._$AV.push(d),c=s[++a]}o!==c?.index&&(r=L.nextNode(),o++)}return L.currentNode=j,i}p(t){let e=0;for(let s of this._$AV)s!==void 0&&(s.strings!==void 0?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}},et=class n{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,i){this.type=2,this._$AH=l,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=q(this,t,e),G(t)?t===l||t==null||t===""?(this._$AH!==l&&this._$AR(),this._$AH=l):t!==this._$AH&&t!==U&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):ne(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==l&&G(this._$AH)?this._$AA.nextSibling.data=t:this.T(j.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:s}=t,i=typeof s=="number"?this._$AC(t):(s.el===void 0&&(s.el=tt.createElement(Vt(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{let r=new ft(i,this),o=r.u(this.options);r.p(e),this.T(o),this._$AH=r}}_$AC(t){let e=It.get(t.strings);return e===void 0&&It.set(t.strings,e=new tt(t)),e}k(t){wt(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,s,i=0;for(let r of t)i===e.length?e.push(s=new n(this.O(Q()),this.O(Q()),this,this.options)):s=e[i],s._$AI(r),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let s=Ot(t).nextSibling;Ot(t).remove(),t=s}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},F=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,r){this.type=1,this._$AH=l,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=r,s.length>2||s[0]!==""||s[1]!==""?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=l}_$AI(t,e=this,s,i){let r=this.strings,o=!1;if(r===void 0)t=q(this,t,e,0),o=!G(t)||t!==this._$AH&&t!==U,o&&(this._$AH=t);else{let a=t,c,d;for(t=r[0],c=0;c<r.length-1;c++)d=q(this,a[s+c],e,c),d===U&&(d=this._$AH[c]),o||=!G(d)||d!==this._$AH[c],d===l?t=l:t!==l&&(t+=(d??"")+r[c+1]),this._$AH[c]=d}o&&!i&&this.j(t)}j(t){t===l?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},vt=class extends F{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===l?void 0:t}},yt=class extends F{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==l)}},bt=class extends F{constructor(t,e,s,i,r){super(t,e,s,i,r),this.type=5}_$AI(t,e=this){if((t=q(this,t,e,0)??l)===U)return;let s=this._$AH,i=t===l&&s!==l||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,r=t!==l&&(s===l||i);i&&this.element.removeEventListener(this.name,this,s),r&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},$t=class{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){q(this,t)}};var ae=xt.litHtmlPolyfillSupport;ae?.(tt,et),(xt.litHtmlVersions??=[]).push("3.3.3");var Wt=(n,t,e)=>{let s=e?.renderBefore??t,i=s._$litPart$;if(i===void 0){let r=e?.renderBefore??null;s._$litPart$=i=new et(t.insertBefore(Q(),r),r,void 0,e??{})}return i._$AI(n),i};var Et=globalThis,b=class extends C{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=Wt(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return U}};b._$litElement$=!0,b.finalized=!0,Et.litElementHydrateSupport?.({LitElement:b});var ce=Et.litElementPolyfillSupport;ce?.({LitElement:b});(Et.litElementVersions??=[]).push("4.2.2");var H=n=>(t,e)=>{e!==void 0?e.addInitializer(()=>{customElements.define(n,t)}):customElements.define(n,t)};var le={attribute:!0,type:String,converter:Z,reflect:!1,hasChanged:ct},he=(n=le,t,e)=>{let{kind:s,metadata:i}=e,r=globalThis.litPropertyMetadata.get(i);if(r===void 0&&globalThis.litPropertyMetadata.set(i,r=new Map),s==="setter"&&((n=Object.create(n)).wrapped=!0),r.set(e.name,n),s==="accessor"){let{name:o}=e;return{set(a){let c=t.get.call(this);t.set.call(this,a),this.requestUpdate(o,c,n,!0,a)},init(a){return a!==void 0&&this.C(o,void 0,n,a),a}}}if(s==="setter"){let{name:o}=e;return function(a){let c=this[o];t.call(this,a),this.requestUpdate(o,c,n,!0,a)}}throw Error("Unsupported decorator location: "+s)};function x(n){return(t,e)=>typeof e=="object"?he(n,t,e):((s,i,r)=>{let o=i.hasOwnProperty(r);return i.constructor.createProperty(r,s),o?Object.getOwnPropertyDescriptor(i,r):void 0})(n,t,e)}function R(n){return x({...n,state:!0,attribute:!1})}var k="goe_steve";function st(n){let t=new Map;for(let e of Object.values(n.entities))if(!(e.platform!==k||!e.device_id)&&!t.has(e.device_id)){let s=n.devices[e.device_id];t.set(e.device_id,s?.name_by_user||s?.name||e.device_id)}return[...t.entries()].map(([e,s])=>({id:e,name:s}))}function dt(n,t){let e={tag_energy:[]};if(!t){let r=st(n);r.length===1&&(t=r[0].id)}if(e.deviceId=t,!t)return e;let s=Object.values(n.entities).filter(r=>r.platform===k&&r.device_id===t),i=r=>{let o=s.find(c=>c.translation_key===r);return o?o.entity_id:s.find(c=>{let d=c.entity_id.split(".")[1]??"";return d===r||d.endsWith(`_${r}`)})?.entity_id};return e.status=i("status"),e.power_flow=i("power_flow"),e.surplus=i("surplus_for_car"),e.target_current=i("target_current"),e.controlling=i("controlling"),e.charging_mode=i("charging_mode"),e.battery_policy=i("battery_policy"),e.smart_control=i("smart_control"),e.auto_phase=i("auto_phase"),e.battery_reserve_soc=i("battery_reserve_soc"),e.battery_floor_soc=i("battery_floor_soc"),e.target_energy=i("target_energy"),e.price_forecast=i("price_forecast"),e.cheap_price=i("cheap_price"),e.active_transaction=i("active_transaction"),e.last_session_energy=i("last_session_energy"),e.selected_tag=i("selected_tag"),e.tag_energy=s.filter(r=>r.translation_key==="tag_energy"||r.entity_id.split(".")[1]?.includes("_tag_energy_")).map(r=>r.entity_id).sort(),e}var At={"card.no_device":"No {name} device found. Set one up first, then add this card.","card.default_title":"Smart Charging","flow.solar":"Solar","flow.grid":"Grid","flow.export":"Export","flow.battery":"Battery","flow.home":"Home","flow.car":"Car","flow.no_car":"No car","control.mode":"Mode","control.battery":"Battery","control.smart_control":"Smart control","control.auto_phase":"Auto phase (1\u21943)","control.battery_fill_to":"Fill battery to","control.battery_use_to":"Use battery down to","control.target_energy":"Car target energy","control.tag":"Tag","action.authorize":"Authorize","action.start":"Start","action.stop":"Stop","session.none":"No active session","session.charging":"Charging: {state}","session.last":"Last session: {energy}","session.blocked":"blocked","session.tag":"tag","editor.device":"Smart Charging device (optional \u2014 auto-detected)","editor.title":"Title (optional)","editor.show_flow":"Show energy flow","editor.show_controls":"Show controls","editor.show_sessions":"Show sessions & RFID","editor.hours":"Hours to show (optional)","price.title":"Electricity price","price.no_price":"No price forecast available. Configure a price sensor for {name} first.","price.cheap_threshold":"Cheap below","price.cheap_hours":"{hours} cheap upcoming","price.next_window":"next {start}\u2013{end}","price.no_cheap":"No cheap hours coming up at this threshold","price.now":"now","price.tomorrow":"Tomorrow"},de={"card.no_device":"Kein {name}-Ger\xE4t gefunden. Richte zuerst eines ein und f\xFCge dann diese Karte hinzu.","card.default_title":"Intelligentes Laden","flow.solar":"Solar","flow.grid":"Netz","flow.export":"Einspeisung","flow.battery":"Batterie","flow.home":"Haus","flow.car":"Auto","flow.no_car":"Kein Auto","control.mode":"Modus","control.battery":"Batterie","control.smart_control":"Intelligente Steuerung","control.auto_phase":"Auto-Phase (1\u21943)","control.battery_fill_to":"Batterie laden bis","control.battery_use_to":"Batterie nutzen bis","control.target_energy":"Ziel-Energie Auto","control.tag":"Tag","action.authorize":"Freigeben","action.start":"Starten","action.stop":"Stoppen","session.none":"Kein aktiver Ladevorgang","session.charging":"L\xE4dt: {state}","session.last":"Letzter Ladevorgang: {energy}","session.blocked":"gesperrt","session.tag":"Tag","editor.device":"Smart-Charging-Ger\xE4t (optional \u2014 automatisch erkannt)","editor.title":"Titel (optional)","editor.show_flow":"Energiefluss anzeigen","editor.show_controls":"Steuerung anzeigen","editor.show_sessions":"Ladevorg\xE4nge & RFID anzeigen","editor.hours":"Anzuzeigende Stunden (optional)","price.title":"Strompreis","price.no_price":"Keine Preisprognose verf\xFCgbar. Richte zuerst einen Preissensor f\xFCr {name} ein.","price.cheap_threshold":"G\xFCnstig unter","price.cheap_hours":"{hours} g\xFCnstig in K\xFCrze","price.next_window":"n\xE4chste {start}\u2013{end}","price.no_cheap":"Bei dieser Schwelle keine g\xFCnstigen Stunden in Sicht","price.now":"jetzt","price.tomorrow":"Morgen"},pe={en:At,de};function ue(n){let t=(n?.locale?.language||n?.language||"en").toLowerCase().split("-")[0];return pe[t]??At}function $(n,t,e={}){let i=ue(n)[t]??At[t]??t;for(let[r,o]of Object.entries(e))i=i.replace(`{${r}}`,o);return i}var D=class extends b{constructor(){super(...arguments);this._schema=[{name:"device",selector:{device:{integration:k}}},{name:"title",selector:{text:{}}},{type:"grid",name:"",schema:[{name:"show_flow",selector:{boolean:{}}},{name:"show_controls",selector:{boolean:{}}},{name:"show_sessions",selector:{boolean:{}}}]}];this._label=e=>{switch(e.name){case"device":return $(this.hass,"editor.device");case"title":return $(this.hass,"editor.title");case"show_flow":return $(this.hass,"editor.show_flow");case"show_controls":return $(this.hass,"editor.show_controls");case"show_sessions":return $(this.hass,"editor.show_sessions");default:return e.name}}}setConfig(e){this._config=e}render(){return!this.hass||!this._config?l:p`<ha-form
      .hass=${this.hass}
      .data=${this._config}
      .schema=${this._schema}
      .computeLabel=${this._label}
      @value-changed=${this._valueChanged}
    ></ha-form>`}_valueChanged(e){let s={...e.detail.value};this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:s},bubbles:!0,composed:!0}))}};D.styles=A`
    ha-form {
      display: block;
      padding: 8px 0;
    }
  `,f([x({attribute:!1})],D.prototype,"hass",2),f([R()],D.prototype,"_config",2),D=f([H("goe-steve-card-editor")],D);var I=class extends b{constructor(){super(...arguments);this._schema=[{name:"device",selector:{device:{integration:k}}},{name:"title",selector:{text:{}}},{name:"hours",selector:{number:{min:6,max:48,mode:"box",unit_of_measurement:"h"}}}];this._label=e=>{switch(e.name){case"device":return $(this.hass,"editor.device");case"title":return $(this.hass,"editor.title");case"hours":return $(this.hass,"editor.hours");default:return e.name}}}setConfig(e){this._config=e}render(){return!this.hass||!this._config?l:p`<ha-form
      .hass=${this.hass}
      .data=${this._config}
      .schema=${this._schema}
      .computeLabel=${this._label}
      @value-changed=${this._valueChanged}
    ></ha-form>`}_valueChanged(e){let s={...e.detail.value};this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:s},bubbles:!0,composed:!0}))}};I.styles=A`
    ha-form {
      display: block;
      padding: 8px 0;
    }
  `,f([x({attribute:!1})],I.prototype,"hass",2),f([R()],I.prototype,"_config",2),I=f([H("goe-steve-price-card-editor")],I);var ge="go-e + SteVe Smart Charging",V=480,ut=200,m={left:38,right:10,top:12,bottom:24},me=V-m.left-m.right,Ct=ut-m.top-m.bottom,pt=36e5,P=class extends b{constructor(){super(...arguments);this._dragValue=null;this._dragging=!1;this._cheapCache=null}static getConfigElement(){return document.createElement("goe-steve-price-card-editor")}static getStubConfig(e){return{type:"custom:goe-steve-price-card",device:st(e)[0]?.id}}setConfig(e){this._config={...e}}getCardSize(){return 6}get _entities(){return this.hass?dt(this.hass,this._config?.device):null}_t(e,s={}){return $(this.hass,e,s)}_stateObj(e){return e?this.hass.states[e]:void 0}_deviceName(e){if(!e)return null;let s=this.hass.devices[e];return s?.name_by_user||s?.name||null}_slots(e){let i=(e.attributes.slots??[]).map(r=>({start:Date.parse(r.start??""),price:Number(r.price)})).filter(r=>!Number.isNaN(r.start)&&!Number.isNaN(r.price)).sort((r,o)=>r.start-o.start);return i.map((r,o)=>({start:r.start,end:o+1<i.length?i[o+1].start:r.start+pt,price:r.price}))}_cheap(e,s){let i=this._stateObj(e.cheap_price),r=Number(s.attributes.cheap_price),o=i?Number(i.state):Number.isNaN(r)?.15:r,a=i?.attributes??{};return{obj:i,value:o,min:Number(a.min??0),max:Number(a.max??1),step:Number(a.step??.01),unit:s.attributes.unit??a.unit_of_measurement??""}}render(){if(!this.hass||!this._config)return l;let e=this._entities,s=this._stateObj(e?.price_forecast),i=s?this._slots(s):[],r=this._config.title??this._deviceName(e?.deviceId)??this._t("price.title");if(!s||i.length===0){let[c,d]=this._t("price.no_price").split("{name}");return p`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:cash-clock"></ha-icon>
          <p>${c}<b>${ge}</b>${d??""}</p>
        </div>
      </ha-card>`}let o=this._cheap(e,s),a=this._dragValue??o.value;return p`<ha-card>
      <div class="header">
        <div class="title-row">
          <ha-icon icon="mdi:cash-clock"></ha-icon>
          <span class="title">${r}</span>
        </div>
        <div class="now-price">${this._fmtPrice(Number(s.state),o.unit)}</div>
      </div>
      ${this._renderChart(i,a)}
      ${this._renderPreview(i,a)}
      ${this._renderThresholdInput(o,a)}
    </ha-card>`}_shownSlots(e){let s=Date.now(),i=e.filter(r=>r.end>s);if(i.length===0&&(i=e.slice(-1)),this._config.hours&&this._config.hours>0){let r=s+this._config.hours*pt;i=i.filter(o=>o.start<r)}return i.slice(0,96)}_renderChart(e,s){let i=Date.now(),r=this._shownSlots(e),o=r[0].start,a=r[r.length-1].end,c=r.map(_=>_.price),d=Math.min(...c,s),u=Math.max(...c,s),h=u-d||1,g=d-h*.1,v=u+h*.1,y=_=>m.left+(_-o)/(a-o)*me,w=_=>m.top+(1-(_-g)/(v-g))*Ct,T=m.top+Ct,S=w(s),W=r.map(_=>{let E=y(_.start),O=y(_.end),Rt=w(_.price),Kt=_.price<=s;return N`<rect
        class="bar ${Kt?"cheap":""}"
        x=${E+.5}
        y=${Rt}
        width=${Math.max(.5,O-E-1)}
        height=${Math.max(0,T-Rt)}
      ></rect>`}),K=[];for(let _ of r){let E=new Date(_.start);if(E.getHours()===0&&E.getMinutes()===0&&_.start>o){let O=y(_.start);K.push(N`<line class="day-div" x1=${O} y1=${m.top} x2=${O} y2=${T}></line>`),K.push(N`<text class="day-lbl" x=${O+3} y=${m.top+9}>${this._t("price.tomorrow")}</text>`)}}let Nt=[];for(let _ of r){let E=new Date(_.start);if(E.getHours()%6===0&&E.getMinutes()===0){let O=y(_.start);Nt.push(N`<text class="x-tick" x=${O} y=${ut-8}>${String(E.getHours()).padStart(2,"0")}</text>`)}}let rt=i>=o&&i<=a?y(i):null;return p`<div class="chart">
      <svg
        viewBox="0 0 ${V} ${ut}"
        preserveAspectRatio="none"
        @pointermove=${this._onPointerMove}
        @pointerup=${this._onPointerUp}
        @pointercancel=${this._onPointerUp}
      >
        <!-- y grid: min / threshold / max -->
        <text class="y-tick" x=${m.left-4} y=${w(v)+3}>${this._fmtNum(u)}</text>
        <text class="y-tick" x=${m.left-4} y=${T}>${this._fmtNum(d)}</text>
        ${K}
        ${W}
        ${Nt}
        ${rt!==null?N`<line class="now-line" x1=${rt} y1=${m.top} x2=${rt} y2=${T}></line>
                 <text class="now-tick" x=${rt} y=${m.top-2}>${this._t("price.now")}</text>`:l}
        <!-- threshold line + draggable handle -->
        <line class="thresh" x1=${m.left} y1=${S} x2=${V-m.right} y2=${S}></line>
        <g class="handle" data-handle @pointerdown=${this._onPointerDown}>
          <!-- generous, invisible touch target so fingers can grab the handle -->
          <rect class="handle-hit" x=${V-m.right-68} y=${S-20} width="72" height="40"></rect>
          <rect class="handle-chip" x=${V-m.right-52} y=${S-9} width="52" height="18" rx="4"></rect>
          <text x=${V-m.right-26} y=${S+4}>${this._fmtNum(s)}</text>
        </g>
      </svg>
    </div>`}_onPointerDown(e){let s=this._entities,i=this._stateObj(s?.price_forecast);!s||!i||!s.cheap_price||(this._cheapCache=this._cheap(s,i),this._dragging=!0,e.target.setPointerCapture?.(e.pointerId),e.preventDefault(),this._updateDrag(e))}_onPointerMove(e){this._dragging&&(e.preventDefault(),this._updateDrag(e))}_onPointerUp(){if(!this._dragging)return;this._dragging=!1;let e=this._cheapCache,s=this._dragValue;this._dragValue=null,this._cheapCache=null,e?.obj&&s!==null&&s!==e.value&&this.hass.callService("number","set_value",{entity_id:e.obj.entity_id,value:s})}_updateDrag(e){let s=this._cheapCache;if(!s)return;let i=this.renderRoot.querySelector("svg");if(!i)return;let r=i.getBoundingClientRect(),o=(e.clientY-r.top)/r.height*ut,{yMin:a,yMax:c}=this._yDomain(s),d=1-(o-m.top)/Ct,u=a+d*(c-a);u=Math.min(s.max,Math.max(s.min,u)),s.step>0&&(u=Math.round(u/s.step)*s.step);let h=(String(s.step).split(".")[1]??"").length||2;this._dragValue=Number(u.toFixed(h))}_yDomain(e){let s=this._entities,i=this._stateObj(s?.price_forecast),r=i?this._slots(i):[],o=this._shownSlots(r),a=this._dragValue??e.value,c=o.map(g=>g.price),d=Math.min(...c,a),u=Math.max(...c,a),h=u-d||1;return{yMin:d-h*.1,yMax:u+h*.1}}_renderPreview(e,s){let i=Date.now(),o=e.filter(h=>h.end>i).filter(h=>h.price<=s);if(o.length===0)return p`<div class="preview muted">
        <ha-icon icon="mdi:flash-off"></ha-icon><span>${this._t("price.no_cheap")}</span>
      </div>`;let a=o.reduce((h,g)=>h+(Math.min(g.end,i+48*pt)-Math.max(g.start,i))/pt,0),c=o[0],d=c.end;for(let h=1;h<o.length&&o[h].start===d;h++)d=o[h].end;let u=`${a.toFixed(a<10?1:0)} h`;return p`<div class="preview">
      <ha-icon icon="mdi:flash"></ha-icon>
      <span>${this._t("price.cheap_hours",{hours:u})}</span>
      <span class="sep">·</span>
      <span class="muted"
        >${this._t("price.next_window",{start:this._fmtTime(Math.max(c.start,i)),end:this._fmtTime(d)})}</span
      >
    </div>`}_renderThresholdInput(e,s){return e.obj?p`<div class="threshold-row">
      <span class="thr-label">${this._t("price.cheap_threshold")}</span>
      <span class="thr-input">
        <input
          type="number"
          .value=${String(s)}
          min=${e.min}
          max=${e.max}
          step=${e.step}
          @change=${i=>this._setThreshold(e,i.target.value)}
        />
        ${e.unit?p`<span class="thr-unit">${e.unit}</span>`:l}
      </span>
    </div>`:l}_setThreshold(e,s){let i=Number(s);!e.obj||Number.isNaN(i)||i===e.value||this.hass.callService("number","set_value",{entity_id:e.obj.entity_id,value:i})}_fmtNum(e){return e.toFixed(Math.abs(e)<1?2:1)}_fmtPrice(e,s){return Number.isNaN(e)?"\u2014":`${this._fmtNum(e)}${s?` ${s}`:""}`}_fmtTime(e){return new Date(e).toLocaleTimeString(this.hass?.locale?.language??[],{hour:"2-digit",minute:"2-digit"})}};P.styles=A`
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
  `,f([x({attribute:!1})],P.prototype,"hass",2),f([R()],P.prototype,"_config",2),f([R()],P.prototype,"_dragValue",2),P=f([H("goe-steve-price-card")],P);window.customCards=window.customCards||[];window.customCards.push({type:"goe-steve-price-card",name:"go-e + SteVe Price",description:"Electricity-price forecast with a draggable 'cheap' threshold \u2014 see the curve and set what counts as cheap.",preview:!0,documentationURL:"https://github.com/JustChr/HAgoe_steve"});var _e="go-e + SteVe Smart Charging",it=n=>{if(n==null||Number.isNaN(n))return"\u2014";let t=Math.abs(n);return t>=1e3?`${(n/1e3).toFixed(t>=1e4?0:1)} kW`:`${Math.round(n)} W`},B=class extends b{static getConfigElement(){return document.createElement("goe-steve-card-editor")}static getStubConfig(t){return{type:"custom:goe-steve-card",device:st(t)[0]?.id}}setConfig(t){this._config={show_flow:!0,show_controls:!0,show_sessions:!0,...t}}getCardSize(){return 8}get _entities(){return this.hass?dt(this.hass,this._config?.device):null}_t(t,e={}){return $(this.hass,t,e)}render(){if(!this.hass||!this._config)return l;let t=this._entities;if(!t||!t.deviceId)return p`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:ev-station"></ha-icon>
          <p>${this._renderNoDevice()}</p>
        </div>
      </ha-card>`;let e=this._config.title??this._deviceName(t.deviceId)??this._t("card.default_title");return p`<ha-card>
      ${this._renderHeader(t,e)}
      <div class="content">
        ${this._config.show_flow?this._renderFlow(t):l}
        ${this._config.show_controls?this._renderControls(t):l}
        ${this._config.show_sessions?this._renderSessions(t):l}
      </div>
    </ha-card>`}_renderNoDevice(){let[t,e]=this._t("card.no_device").split("{name}");return p`${t}<b>${_e}</b>${e??""}`}_renderHeader(t,e){let s=this._stateObj(t.status),i=s?.state&&s.state!=="unknown"?s.state:"\u2014",r=this._isOn(t.controlling),o=this._displayState(t.charging_mode),a=this._displayState(t.battery_policy);return p`<div class="header">
      <div class="title-row">
        <ha-icon class="brain ${r?"active":""}" icon="mdi:brain"></ha-icon>
        <span class="title">${e}</span>
      </div>
      <div class="reason">${i}</div>
      <div class="chips">
        ${o?p`<span class="chip"><ha-icon icon="mdi:ev-station"></ha-icon>${o}</span>`:l}
        ${a?p`<span class="chip"><ha-icon icon="mdi:home-battery"></ha-icon>${a}</span>`:l}
      </div>
    </div>`}_renderFlow(t){let e=this._stateObj(t.power_flow),s=e?.attributes??{},i=Number(s.pv_w??NaN),r=Number(s.grid_w??NaN),o=s.battery_w===null||s.battery_w===void 0?null:Number(s.battery_w),a=Number(s.car_w??(e?e.state:NaN)),c=Number(s.house_w??NaN),d=s.battery_soc,u=s.car_connected,h=50,g=(y,w,T,S,W,K="")=>N`
      <g class="node" transform="translate(${y},${w})">
        <circle r="26"></circle>
        <foreignObject x="-13" y="-20" width="26" height="26">
          <ha-icon icon="${T}"></ha-icon>
        </foreignObject>
        <text class="node-val" y="14">${W}</text>
        <text class="node-lbl" y="42">${S}${K}</text>
      </g>`,v=(y,w,T,S)=>{let W=w?Math.max(.6,3-Math.min(S,9e3)/3e3):0;return N`
        <path class="edge" d="${y}"></path>
        <path
          class="edge-flow ${w?"active":""} ${T?"rev":""}"
          d="${y}"
          style="${w?`animation-duration:${W}s`:""}"
        ></path>`};return p`<div class="flow">
      <svg viewBox="0 0 320 336" preserveAspectRatio="xMidYMid meet">
        ${v("M160,66 L160,134",i>h,!1,i)}
        ${v("M76,160 L134,160",Number.isNaN(r)?!1:Math.abs(r)>h,r<0,Math.abs(r))}
        ${o!==null?v("M244,160 L186,160",Math.abs(o)>h,o>0,Math.abs(o)):l}
        ${v("M160,186 L160,244",a>h,!1,a)}

        ${g(160,40,"mdi:solar-power",this._t("flow.solar"),it(i))}
        ${g(40,160,"mdi:transmission-tower",r<0?this._t("flow.export"):this._t("flow.grid"),it(Math.abs(r)))}
        ${o!==null?g(280,160,"mdi:home-battery",this._t("flow.battery"),it(Math.abs(o)),d!=null?` ${Math.round(Number(d))}%`:""):l}
        ${g(160,160,"mdi:home",this._t("flow.home"),it(c))}
        ${g(160,280,u===!1?"mdi:car-off":"mdi:car-electric",u===!1?this._t("flow.no_car"):this._t("flow.car"),it(a))}
      </svg>
    </div>`}_renderControls(t){let e=this._stateObj(t.charging_mode),s=this._stateObj(t.battery_policy),i=this._stateObj(t.smart_control),r=this._stateObj(t.battery_reserve_soc),o=this._stateObj(t.battery_floor_soc),a=this._stateObj(t.target_energy),c=s?.state,d=e?.state;return p`<div class="controls">
      ${e?p`<div class="control">
            <span class="ctl-label">${this._t("control.mode")}</span>
            ${this._renderSelect(e)}
          </div>`:l}
      ${s?p`<div class="control">
            <span class="ctl-label">${this._t("control.battery")}</span>
            ${this._renderSelect(s)}
          </div>`:l}
      ${r&&c==="protect"?p`<div class="control">
            <span class="ctl-label">${this._t("control.battery_fill_to")}</span>
            ${this._renderNumber(r)}
          </div>`:l}
      ${r&&c==="share"?p`<div class="control">
            <span class="ctl-label">${this._t("control.battery_use_to")}</span>
            ${this._renderNumber(r)}
          </div>`:l}
      ${o&&c==="assist"?p`<div class="control">
            <span class="ctl-label">${this._t("control.battery_use_to")}</span>
            ${this._renderNumber(o)}
          </div>`:l}
      ${a&&(d==="price"||d==="combined")?p`<div class="control">
            <span class="ctl-label">${this._t("control.target_energy")}</span>
            ${this._renderNumber(a)}
          </div>`:l}
      ${i?p`<div class="control">
            <span class="ctl-label">${this._t("control.smart_control")}</span>
            <ha-switch
              .checked=${this._isOn(t.smart_control)}
              @change=${u=>this._toggle(t.smart_control,u)}
            ></ha-switch>
          </div>`:l}
      ${t.auto_phase?p`<div class="control">
            <span class="ctl-label">${this._t("control.auto_phase")}</span>
            <ha-switch
              .checked=${this._isOn(t.auto_phase)}
              @change=${u=>this._toggle(t.auto_phase,u)}
            ></ha-switch>
          </div>`:l}
    </div>`}_renderNumber(t){let e=t.attributes,s=e.unit_of_measurement??"";return p`<span class="ctl-number-wrap">
      <input
        class="ctl-number"
        type="number"
        .value=${t.state}
        min=${e.min??l}
        max=${e.max??l}
        step=${e.step??l}
        @change=${i=>this._setNumber(t,i.target.value)}
      />
      ${s?p`<span class="ctl-unit">${s}</span>`:l}
    </span>`}_setNumber(t,e){let s=Number(e);Number.isNaN(s)||String(s)===t.state||this.hass.callService("number","set_value",{entity_id:t.entity_id,value:s})}_renderSelect(t){let e=t.attributes.options??[];return p`<select
      class="ctl-select"
      @change=${s=>this._selectOption(t,s.target.value)}
    >
      ${e.map(s=>p`<option .value=${s} ?selected=${s===t.state}>
            ${this._localizeOption(t,s)}
          </option>`)}
    </select>`}_renderSessions(t){let e=this._stateObj(t.active_transaction),s=this._stateObj(t.last_session_energy),i=this._stateObj(t.selected_tag),r=t.tag_energy.map(a=>this._stateObj(a)).filter(a=>!!a);if(!e&&!s&&!i&&r.length===0)return l;let o=!!e&&!["idle","unknown","unavailable",""].includes(e.state);return p`<div class="sessions">
      ${this._renderTagPicker(i,o)}
      ${e?p`<div class="session-row">
            <ha-icon icon="mdi:card-account-details"></ha-icon>
            <span>${e.state==="idle"?this._t("session.none"):this._t("session.charging",{state:e.attributes.name??e.state})}</span>
          </div>`:l}
      ${s&&s.state&&s.state!=="unknown"?p`<div class="session-row">
            <ha-icon icon="mdi:history"></ha-icon>
            <span>${this._t("session.last",{energy:this._fmtState(s)})}</span>
          </div>`:l}
      ${r.length?p`<div class="tags">
            ${r.map(a=>p`<div class="tag">
                <span class="tag-id">${a.attributes.name??a.attributes.id_tag??this._t("session.tag")}</span>
                <span class="tag-kwh ${a.attributes.blocked?"blocked":""}">
                  ${this._fmtState(a)}${a.attributes.blocked?` \xB7 ${this._t("session.blocked")}`:""}
                </span>
              </div>`)}
          </div>`:l}
    </div>`}_renderTagPicker(t,e){if(!t)return l;let s=t.attributes.options??[];if(s.length===0)return l;let i=s.includes(t.state);return p`<div class="tag-picker">
      ${e?l:p`<div class="control">
            <span class="ctl-label">${this._t("control.tag")}</span>
            ${this._renderSelect(t)}
          </div>`}
      <div class="tag-actions">
        ${e?p`<button
              class="tag-btn stop"
              @click=${()=>this._callTagService("remote_stop")}
            >
              <ha-icon icon="mdi:stop"></ha-icon>${this._t("action.stop")}
            </button>`:p`<button
                class="tag-btn"
                ?disabled=${!i}
                @click=${()=>this._callTagService("authorize_tag")}
              >
                <ha-icon icon="mdi:check-decagram"></ha-icon>${this._t("action.authorize")}
              </button>
              <button
                class="tag-btn"
                ?disabled=${!i}
                @click=${()=>this._callTagService("remote_start")}
              >
                <ha-icon icon="mdi:play"></ha-icon>${this._t("action.start")}
              </button>`}
      </div>
    </div>`}_callTagService(t){this.hass.callService(k,t,{})}_stateObj(t){return t?this.hass.states[t]:void 0}_isOn(t){return this._stateObj(t)?.state==="on"}_displayState(t){let e=this._stateObj(t);return e?this._fmtState(e):null}_fmtState(t){return this.hass.formatEntityState?this.hass.formatEntityState(t):t.state}_localizeOption(t,e){let s=this.hass.entities?.[t.entity_id]?.translation_key;if(s){let i=`component.${k}.entity.select.${s}.state.${e}`,r=this.hass.localize?.(i);if(r)return r}if(this.hass.formatEntityState){let i=this.hass.formatEntityState({...t,state:e},e);if(i)return i}return e}_deviceName(t){let e=this.hass.devices[t];return e?.name_by_user||e?.name||null}_selectOption(t,e){e!==t.state&&this.hass.callService("select","select_option",{entity_id:t.entity_id,option:e})}_toggle(t,e){if(!t)return;let s=e.target.checked;this.hass.callService("switch",s?"turn_on":"turn_off",{entity_id:t})}};B.styles=A`
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
  `,f([x({attribute:!1})],B.prototype,"hass",2),f([R()],B.prototype,"_config",2),B=f([H("goe-steve-card")],B);window.customCards=window.customCards||[];window.customCards.push({type:"goe-steve-card",name:"go-e + SteVe Smart Charging",description:"Live energy flow, charging mode & battery policy with the brain's reasoning, inline controls and per-RFID energy.",preview:!0,documentationURL:"https://github.com/JustChr/HAgoe_steve"});export{B as GoeSteveCard};
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/lit-html.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-element/lit-element.js:
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

@lit/reactive-element/decorators/custom-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/property.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/state.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/event-options.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/base.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-all.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-async.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-assigned-elements.js:
  (**
   * @license
   * Copyright 2021 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/decorators/query-assigned-nodes.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
