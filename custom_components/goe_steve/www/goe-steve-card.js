/* go-e + SteVe Smart Charging card — bundled, do not edit by hand. Source in /card. */
var Zt=Object.defineProperty;var Yt=Object.getOwnPropertyDescriptor;var f=(a,s,t,e)=>{for(var r=e>1?void 0:e?Yt(s,t):s,i=a.length-1,n;i>=0;i--)(n=a[i])&&(r=(e?n(s,t,r):n(r))||r);return e&&r&&Zt(s,t,r),r};var ct=globalThis,lt=ct.ShadowRoot&&(ct.ShadyCSS===void 0||ct.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,ft=Symbol(),Ct=new WeakMap,Z=class{constructor(s,t,e){if(this._$cssResult$=!0,e!==ft)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=s,this.t=t}get styleSheet(){let s=this.o,t=this.t;if(lt&&s===void 0){let e=t!==void 0&&t.length===1;e&&(s=Ct.get(t)),s===void 0&&((this.o=s=new CSSStyleSheet).replaceSync(this.cssText),e&&Ct.set(t,s))}return s}toString(){return this.cssText}},zt=a=>new Z(typeof a=="string"?a:a+"",void 0,ft),T=(a,...s)=>{let t=a.length===1?a[0]:s.reduce((e,r,i)=>e+(n=>{if(n._$cssResult$===!0)return n.cssText;if(typeof n=="number")return n;throw Error("Value passed to 'css' function must be a 'css' function result: "+n+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(r)+a[i+1],a[0]);return new Z(t,a,ft)},Pt=(a,s)=>{if(lt)a.adoptedStyleSheets=s.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(let t of s){let e=document.createElement("style"),r=ct.litNonce;r!==void 0&&e.setAttribute("nonce",r),e.textContent=t.cssText,a.appendChild(e)}},bt=lt?a=>a:a=>a instanceof CSSStyleSheet?(s=>{let t="";for(let e of s.cssRules)t+=e.cssText;return zt(t)})(a):a;var{is:Qt,defineProperty:Xt,getOwnPropertyDescriptor:te,getOwnPropertyNames:ee,getOwnPropertySymbols:re,getPrototypeOf:se}=Object,ht=globalThis,Ht=ht.trustedTypes,ie=Ht?Ht.emptyScript:"",ne=ht.reactiveElementPolyfillSupport,Y=(a,s)=>a,Q={toAttribute(a,s){switch(s){case Boolean:a=a?ie:null;break;case Object:case Array:a=a==null?a:JSON.stringify(a)}return a},fromAttribute(a,s){let t=a;switch(s){case Boolean:t=a!==null;break;case Number:t=a===null?null:Number(a);break;case Object:case Array:try{t=JSON.parse(a)}catch{t=null}}return t}},pt=(a,s)=>!Qt(a,s),Ot={attribute:!0,type:String,converter:Q,reflect:!1,useDefault:!1,hasChanged:pt};Symbol.metadata??=Symbol("metadata"),ht.litPropertyMetadata??=new WeakMap;var M=class extends HTMLElement{static addInitializer(s){this._$Ei(),(this.l??=[]).push(s)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(s,t=Ot){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(s)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(s,t),!t.noAccessor){let e=Symbol(),r=this.getPropertyDescriptor(s,e,t);r!==void 0&&Xt(this.prototype,s,r)}}static getPropertyDescriptor(s,t,e){let{get:r,set:i}=te(this.prototype,s)??{get(){return this[t]},set(n){this[t]=n}};return{get:r,set(n){let o=r?.call(this);i?.call(this,n),this.requestUpdate(s,o,e)},configurable:!0,enumerable:!0}}static getPropertyOptions(s){return this.elementProperties.get(s)??Ot}static _$Ei(){if(this.hasOwnProperty(Y("elementProperties")))return;let s=se(this);s.finalize(),s.l!==void 0&&(this.l=[...s.l]),this.elementProperties=new Map(s.elementProperties)}static finalize(){if(this.hasOwnProperty(Y("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(Y("properties"))){let t=this.properties,e=[...ee(t),...re(t)];for(let r of e)this.createProperty(r,t[r])}let s=this[Symbol.metadata];if(s!==null){let t=litPropertyMetadata.get(s);if(t!==void 0)for(let[e,r]of t)this.elementProperties.set(e,r)}this._$Eh=new Map;for(let[t,e]of this.elementProperties){let r=this._$Eu(t,e);r!==void 0&&this._$Eh.set(r,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(s){let t=[];if(Array.isArray(s)){let e=new Set(s.flat(1/0).reverse());for(let r of e)t.unshift(bt(r))}else s!==void 0&&t.push(bt(s));return t}static _$Eu(s,t){let e=t.attribute;return e===!1?void 0:typeof e=="string"?e:typeof s=="string"?s.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(s=>this.enableUpdating=s),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(s=>s(this))}addController(s){(this._$EO??=new Set).add(s),this.renderRoot!==void 0&&this.isConnected&&s.hostConnected?.()}removeController(s){this._$EO?.delete(s)}_$E_(){let s=new Map,t=this.constructor.elementProperties;for(let e of t.keys())this.hasOwnProperty(e)&&(s.set(e,this[e]),delete this[e]);s.size>0&&(this._$Ep=s)}createRenderRoot(){let s=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return Pt(s,this.constructor.elementStyles),s}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(s=>s.hostConnected?.())}enableUpdating(s){}disconnectedCallback(){this._$EO?.forEach(s=>s.hostDisconnected?.())}attributeChangedCallback(s,t,e){this._$AK(s,e)}_$ET(s,t){let e=this.constructor.elementProperties.get(s),r=this.constructor._$Eu(s,e);if(r!==void 0&&e.reflect===!0){let i=(e.converter?.toAttribute!==void 0?e.converter:Q).toAttribute(t,e.type);this._$Em=s,i==null?this.removeAttribute(r):this.setAttribute(r,i),this._$Em=null}}_$AK(s,t){let e=this.constructor,r=e._$Eh.get(s);if(r!==void 0&&this._$Em!==r){let i=e.getPropertyOptions(r),n=typeof i.converter=="function"?{fromAttribute:i.converter}:i.converter?.fromAttribute!==void 0?i.converter:Q;this._$Em=r;let o=n.fromAttribute(t,i.type);this[r]=o??this._$Ej?.get(r)??o,this._$Em=null}}requestUpdate(s,t,e,r=!1,i){if(s!==void 0){let n=this.constructor;if(r===!1&&(i=this[s]),e??=n.getPropertyOptions(s),!((e.hasChanged??pt)(i,t)||e.useDefault&&e.reflect&&i===this._$Ej?.get(s)&&!this.hasAttribute(n._$Eu(s,e))))return;this.C(s,t,e)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(s,t,{useDefault:e,reflect:r,wrapped:i},n){e&&!(this._$Ej??=new Map).has(s)&&(this._$Ej.set(s,n??t??this[s]),i!==!0||n!==void 0)||(this._$AL.has(s)||(this.hasUpdated||e||(t=void 0),this._$AL.set(s,t)),r===!0&&this._$Em!==s&&(this._$Eq??=new Set).add(s))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}let s=this.scheduleUpdate();return s!=null&&await s,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[r,i]of this._$Ep)this[r]=i;this._$Ep=void 0}let e=this.constructor.elementProperties;if(e.size>0)for(let[r,i]of e){let{wrapped:n}=i,o=this[r];n!==!0||this._$AL.has(r)||o===void 0||this.C(r,void 0,i,o)}}let s=!1,t=this._$AL;try{s=this.shouldUpdate(t),s?(this.willUpdate(t),this._$EO?.forEach(e=>e.hostUpdate?.()),this.update(t)):this._$EM()}catch(e){throw s=!1,this._$EM(),e}s&&this._$AE(t)}willUpdate(s){}_$AE(s){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(s)),this.updated(s)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(s){return!0}update(s){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(s){}firstUpdated(s){}};M.elementStyles=[],M.shadowRootOptions={mode:"open"},M[Y("elementProperties")]=new Map,M[Y("finalized")]=new Map,ne?.({ReactiveElement:M}),(ht.reactiveElementVersions??=[]).push("2.1.2");var At=globalThis,Dt=a=>a,dt=At.trustedTypes,Lt=dt?dt.createPolicy("lit-html",{createHTML:a=>a}):void 0,Ft="$lit$",P=`lit$${Math.random().toFixed(9).slice(2)}$`,Vt="?"+P,ae=`<${Vt}>`,I=document,tt=()=>I.createComment(""),et=a=>a===null||typeof a!="object"&&typeof a!="function",kt=Array.isArray,oe=a=>kt(a)||typeof a?.[Symbol.iterator]=="function",vt=`[ 	
\f\r]`,X=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,jt=/-->/g,Wt=/>/g,W=RegExp(`>|${vt}(?:([^\\s"'>=/]+)(${vt}*=${vt}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),Ut=/'/g,It=/"/g,qt=/^(?:script|style|textarea|title)$/i,Nt=a=>(s,...t)=>({_$litType$:a,strings:s,values:t}),p=Nt(1),H=Nt(2),Ne=Nt(3),B=Symbol.for("lit-noChange"),u=Symbol.for("lit-nothing"),Bt=new WeakMap,U=I.createTreeWalker(I,129);function Kt(a,s){if(!kt(a)||!a.hasOwnProperty("raw"))throw Error("invalid template strings array");return Lt!==void 0?Lt.createHTML(s):s}var ce=(a,s)=>{let t=a.length-1,e=[],r,i=s===2?"<svg>":s===3?"<math>":"",n=X;for(let o=0;o<t;o++){let c=a[o],l,d,h=-1,g=0;for(;g<c.length&&(n.lastIndex=g,d=n.exec(c),d!==null);)g=n.lastIndex,n===X?d[1]==="!--"?n=jt:d[1]!==void 0?n=Wt:d[2]!==void 0?(qt.test(d[2])&&(r=RegExp("</"+d[2],"g")),n=W):d[3]!==void 0&&(n=W):n===W?d[0]===">"?(n=r??X,h=-1):d[1]===void 0?h=-2:(h=n.lastIndex-d[2].length,l=d[1],n=d[3]===void 0?W:d[3]==='"'?It:Ut):n===It||n===Ut?n=W:n===jt||n===Wt?n=X:(n=W,r=void 0);let _=n===W&&a[o+1].startsWith("/>")?" ":"";i+=n===X?c+ae:h>=0?(e.push(l),c.slice(0,h)+Ft+c.slice(h)+P+_):c+P+(h===-2?o:_)}return[Kt(a,i+(a[t]||"<?>")+(s===2?"</svg>":s===3?"</math>":"")),e]},rt=class a{constructor({strings:s,_$litType$:t},e){let r;this.parts=[];let i=0,n=0,o=s.length-1,c=this.parts,[l,d]=ce(s,t);if(this.el=a.createElement(l,e),U.currentNode=this.el.content,t===2||t===3){let h=this.el.content.firstChild;h.replaceWith(...h.childNodes)}for(;(r=U.nextNode())!==null&&c.length<o;){if(r.nodeType===1){if(r.hasAttributes())for(let h of r.getAttributeNames())if(h.endsWith(Ft)){let g=d[n++],_=r.getAttribute(h).split(P),y=/([.?@])?(.*)/.exec(g);c.push({type:1,index:i,name:y[2],strings:_,ctor:y[1]==="."?$t:y[1]==="?"?xt:y[1]==="@"?wt:K}),r.removeAttribute(h)}else h.startsWith(P)&&(c.push({type:6,index:i}),r.removeAttribute(h));if(qt.test(r.tagName)){let h=r.textContent.split(P),g=h.length-1;if(g>0){r.textContent=dt?dt.emptyScript:"";for(let _=0;_<g;_++)r.append(h[_],tt()),U.nextNode(),c.push({type:2,index:++i});r.append(h[g],tt())}}}else if(r.nodeType===8)if(r.data===Vt)c.push({type:2,index:i});else{let h=-1;for(;(h=r.data.indexOf(P,h+1))!==-1;)c.push({type:7,index:i}),h+=P.length-1}i++}}static createElement(s,t){let e=I.createElement("template");return e.innerHTML=s,e}};function q(a,s,t=a,e){if(s===B)return s;let r=e!==void 0?t._$Co?.[e]:t._$Cl,i=et(s)?void 0:s._$litDirective$;return r?.constructor!==i&&(r?._$AO?.(!1),i===void 0?r=void 0:(r=new i(a),r._$AT(a,t,e)),e!==void 0?(t._$Co??=[])[e]=r:t._$Cl=r),r!==void 0&&(s=q(a,r._$AS(a,s.values),r,e)),s}var yt=class{constructor(s,t){this._$AV=[],this._$AN=void 0,this._$AD=s,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(s){let{el:{content:t},parts:e}=this._$AD,r=(s?.creationScope??I).importNode(t,!0);U.currentNode=r;let i=U.nextNode(),n=0,o=0,c=e[0];for(;c!==void 0;){if(n===c.index){let l;c.type===2?l=new st(i,i.nextSibling,this,s):c.type===1?l=new c.ctor(i,c.name,c.strings,this,s):c.type===6&&(l=new St(i,this,s)),this._$AV.push(l),c=e[++o]}n!==c?.index&&(i=U.nextNode(),n++)}return U.currentNode=I,r}p(s){let t=0;for(let e of this._$AV)e!==void 0&&(e.strings!==void 0?(e._$AI(s,e,t),t+=e.strings.length-2):e._$AI(s[t])),t++}},st=class a{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(s,t,e,r){this.type=2,this._$AH=u,this._$AN=void 0,this._$AA=s,this._$AB=t,this._$AM=e,this.options=r,this._$Cv=r?.isConnected??!0}get parentNode(){let s=this._$AA.parentNode,t=this._$AM;return t!==void 0&&s?.nodeType===11&&(s=t.parentNode),s}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(s,t=this){s=q(this,s,t),et(s)?s===u||s==null||s===""?(this._$AH!==u&&this._$AR(),this._$AH=u):s!==this._$AH&&s!==B&&this._(s):s._$litType$!==void 0?this.$(s):s.nodeType!==void 0?this.T(s):oe(s)?this.k(s):this._(s)}O(s){return this._$AA.parentNode.insertBefore(s,this._$AB)}T(s){this._$AH!==s&&(this._$AR(),this._$AH=this.O(s))}_(s){this._$AH!==u&&et(this._$AH)?this._$AA.nextSibling.data=s:this.T(I.createTextNode(s)),this._$AH=s}$(s){let{values:t,_$litType$:e}=s,r=typeof e=="number"?this._$AC(s):(e.el===void 0&&(e.el=rt.createElement(Kt(e.h,e.h[0]),this.options)),e);if(this._$AH?._$AD===r)this._$AH.p(t);else{let i=new yt(r,this),n=i.u(this.options);i.p(t),this.T(n),this._$AH=i}}_$AC(s){let t=Bt.get(s.strings);return t===void 0&&Bt.set(s.strings,t=new rt(s)),t}k(s){kt(this._$AH)||(this._$AH=[],this._$AR());let t=this._$AH,e,r=0;for(let i of s)r===t.length?t.push(e=new a(this.O(tt()),this.O(tt()),this,this.options)):e=t[r],e._$AI(i),r++;r<t.length&&(this._$AR(e&&e._$AB.nextSibling,r),t.length=r)}_$AR(s=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);s!==this._$AB;){let e=Dt(s).nextSibling;Dt(s).remove(),s=e}}setConnected(s){this._$AM===void 0&&(this._$Cv=s,this._$AP?.(s))}},K=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(s,t,e,r,i){this.type=1,this._$AH=u,this._$AN=void 0,this.element=s,this.name=t,this._$AM=r,this.options=i,e.length>2||e[0]!==""||e[1]!==""?(this._$AH=Array(e.length-1).fill(new String),this.strings=e):this._$AH=u}_$AI(s,t=this,e,r){let i=this.strings,n=!1;if(i===void 0)s=q(this,s,t,0),n=!et(s)||s!==this._$AH&&s!==B,n&&(this._$AH=s);else{let o=s,c,l;for(s=i[0],c=0;c<i.length-1;c++)l=q(this,o[e+c],t,c),l===B&&(l=this._$AH[c]),n||=!et(l)||l!==this._$AH[c],l===u?s=u:s!==u&&(s+=(l??"")+i[c+1]),this._$AH[c]=l}n&&!r&&this.j(s)}j(s){s===u?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,s??"")}},$t=class extends K{constructor(){super(...arguments),this.type=3}j(s){this.element[this.name]=s===u?void 0:s}},xt=class extends K{constructor(){super(...arguments),this.type=4}j(s){this.element.toggleAttribute(this.name,!!s&&s!==u)}},wt=class extends K{constructor(s,t,e,r,i){super(s,t,e,r,i),this.type=5}_$AI(s,t=this){if((s=q(this,s,t,0)??u)===B)return;let e=this._$AH,r=s===u&&e!==u||s.capture!==e.capture||s.once!==e.once||s.passive!==e.passive,i=s!==u&&(e===u||r);r&&this.element.removeEventListener(this.name,this,e),i&&this.element.addEventListener(this.name,this,s),this._$AH=s}handleEvent(s){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,s):this._$AH.handleEvent(s)}},St=class{constructor(s,t,e){this.element=s,this.type=6,this._$AN=void 0,this._$AM=t,this.options=e}get _$AU(){return this._$AM._$AU}_$AI(s){q(this,s)}};var le=At.litHtmlPolyfillSupport;le?.(rt,st),(At.litHtmlVersions??=[]).push("3.3.3");var Gt=(a,s,t)=>{let e=t?.renderBefore??s,r=e._$litPart$;if(r===void 0){let i=t?.renderBefore??null;e._$litPart$=r=new st(s.insertBefore(tt(),i),i,void 0,t??{})}return r._$AI(a),r};var Et=globalThis,w=class extends M{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let s=super.createRenderRoot();return this.renderOptions.renderBefore??=s.firstChild,s}update(s){let t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(s),this._$Do=Gt(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return B}};w._$litElement$=!0,w.finalized=!0,Et.litElementHydrateSupport?.({LitElement:w});var he=Et.litElementPolyfillSupport;he?.({LitElement:w});(Et.litElementVersions??=[]).push("4.2.2");var O=a=>(s,t)=>{t!==void 0?t.addInitializer(()=>{customElements.define(a,s)}):customElements.define(a,s)};var pe={attribute:!0,type:String,converter:Q,reflect:!1,hasChanged:pt},de=(a=pe,s,t)=>{let{kind:e,metadata:r}=t,i=globalThis.litPropertyMetadata.get(r);if(i===void 0&&globalThis.litPropertyMetadata.set(r,i=new Map),e==="setter"&&((a=Object.create(a)).wrapped=!0),i.set(t.name,a),e==="accessor"){let{name:n}=t;return{set(o){let c=s.get.call(this);s.set.call(this,o),this.requestUpdate(n,c,a,!0,o)},init(o){return o!==void 0&&this.C(n,void 0,a,o),o}}}if(e==="setter"){let{name:n}=t;return function(o){let c=this[n];s.call(this,o),this.requestUpdate(n,c,a,!0,o)}}throw Error("Unsupported decorator location: "+e)};function N(a){return(s,t)=>typeof t=="object"?de(a,s,t):((e,r,i)=>{let n=r.hasOwnProperty(i);return r.constructor.createProperty(i,e),n?Object.getOwnPropertyDescriptor(r,i):void 0})(a,s,t)}function S(a){return N({...a,state:!0,attribute:!1})}var C="goe_steve";function it(a){let s=new Map;for(let t of Object.values(a.entities))if(!(t.platform!==C||!t.device_id)&&!s.has(t.device_id)){let e=a.devices[t.device_id];s.set(t.device_id,e?.name_by_user||e?.name||t.device_id)}return[...s.entries()].map(([t,e])=>({id:t,name:e}))}function gt(a,s){let t={tag_energy:[]};if(!s){let i=it(a);i.length===1&&(s=i[0].id)}if(t.deviceId=s,!s)return t;let e=Object.values(a.entities).filter(i=>i.platform===C&&i.device_id===s),r=i=>{let n=e.find(c=>c.translation_key===i);return n?n.entity_id:e.find(c=>{let l=c.entity_id.split(".")[1]??"";return l===i||l.endsWith(`_${i}`)})?.entity_id};return t.status=r("status"),t.power_flow=r("power_flow"),t.surplus=r("surplus_for_car"),t.target_current=r("target_current"),t.controlling=r("controlling"),t.battery_hold=r("battery_hold"),t.charging_mode=r("charging_mode"),t.battery_hold_mode=r("battery_hold_mode"),t.smart_control=r("smart_control"),t.auto_phase=r("auto_phase"),t.manual_charge=r("manual_charge"),t.manual_current=r("manual_current"),t.manual_phases=r("manual_phases"),t.battery_reserve_soc=r("battery_reserve_soc"),t.target_energy=r("target_energy"),t.departure=r("departure"),t.max_current=r("max_current"),t.min_current=r("min_current"),t.price_forecast=r("price_forecast"),t.cheap_price=r("cheap_price"),t.active_transaction=r("active_transaction"),t.last_session_energy=r("last_session_energy"),t.selected_tag=r("selected_tag"),t.tag_energy=e.filter(i=>i.translation_key==="tag_energy"||i.entity_id.split(".")[1]?.includes("_tag_energy_")).map(i=>i.entity_id).sort(),t}var Rt={"card.no_device":"No {name} device found. Set one up first, then add this card.","card.default_title":"Smart Charging","live.live":"live","live.updated_ago":"updated {ago} ago","hero.not_connected":"Not connected","hero.paused":"Paused","hero.paused_ready":"Paused \xB7 ready on {phases} \u03C6","hero.asked_takes":"asked {asked} A, car takes {takes} A","hero.solar_share":"{pct} % solar","source.solar":"Solar","source.battery":"Battery","source.grid":"Grid","source.to_car":"{source} \u2192 car: {watts} of {total}","source.none":"Nothing flowing from {source} right now.","source.tap_hint":"Tap a segment for exact watts.","source.exporting":"House running on PV \u2014 surplus is exporting.","source.paused":"Car paused \u2014 no power flowing.","balance.pv":"PV","balance.house":"House","balance.grid":"Grid","balance.export":"Export","balance.battery":"Battery","balance.idle":"idle","chip.hold":"Battery discharge blocked","chip.hold_manual":"Discharge blocked (manual)","chip.price_cheap":"{price} {unit} \u2014 cheap \u2713","chip.price_wait":"{price} {unit} \u2014 waiting for \u2264 {target}","chip.resume_in":"Can resume in {time}","chip.riding_out":"Riding out dip \xB7 {time}","chip.phases":"{phases} \u03C6","chip.forced_off":"Charger forced off","plan.now":"now","plan.hours_ahead":"+{h} h","plan.drag_hint":"Drag the \u2195 pill to set your cheap-price target.","plan.target_aria":"Cheap-price target, arrow keys to adjust","plan.on_track":"on track","plan.tight":"tight \u2014 few cheap hours","control.home_battery":"Home battery","control.mode":"Mode","control.manual_charge":"Charge now","control.manual_current":"Current","control.manual_phases":"Phases","control.smart_control":"Smart control","control.auto_phase":"Auto phase (1\u21943)","control.battery_reserve":"Keep battery above","control.target_energy":"Car target energy","control.departure":"Departure","control.max_current":"Max current","control.min_current":"Min current","control.tag":"Tag","live.target":"Target","live.surplus":"Surplus","action.start":"Start","action.stop":"Stop","action.start_charging":"Start charging","action.stop_charging":"Stop charging","action.stop_confirm":"Stop the active charging session?","session.none_hint":"No active session \u2014 plug in and pick a tag to start.","reason.smart_disabled":"Smart control disabled","reason.manual_passive":"Manual mode \u2014 charger left as-is","reason.manual_paused":"Manual mode \u2014 paused","reason.manual_charging":"Manual charging at {amps} A","reason.manual_charging_guarded":"Manual charging at {amps} A (protecting home battery)","reason.no_car":"No car connected","reason.fast":"Fast charging at {amps} A","reason.cheap_grid":"Cheap grid {price}/kWh \u2264 {threshold} \u2192 full power","reason.cheap_grid_guarded":"Cheap grid {price}/kWh \u2264 {threshold} \u2192 full power (protecting home battery \u2192 {amps} A)","reason.deadline_plan":"Planned cheap hour at {price}/kWh \u2014 {remaining} kWh to go by departure","reason.deadline_plan_guarded":"Planned cheap hour at {price}/kWh \u2014 {remaining} kWh to go by departure (protecting home battery \u2192 {amps} A)","reason.deadline_urgent":"Charging now to make the departure target \u2014 {remaining} kWh to go","reason.target_reached":"Departure target reached \u2014 {delivered} kWh charged","reason.plan_waiting":"Waiting for a planned cheap hour","reason.waiting_battery_reserve":"Waiting \u2014 home battery {soc}% < reserve {reserve}%","reason.waiting_surplus":"Waiting for surplus \u2014 {surplus} W < {needed} W needed","reason.surplus_confirm":"Surplus {surplus} W \u2014 confirming before start","reason.surplus_ride_out":"Surplus dipped \u2014 riding it out at {amps} A","reason.solar_surplus":"Solar surplus {surplus} W \u2192 {amps} A","reason.solar_surplus_phase":"Solar surplus {surplus} W \u2192 {amps} A ({phases}-phase)","reason.solar_surplus_eased":"Solar surplus {surplus} W \u2192 {amps} A (easing off home battery)","reason.solar_min_topup":"Minimum {amps} A (surplus only {surplus} W, topping up from grid)","session.none":"No active session","session.charging":"Charging: {state}","session.last":"Last session: {energy}","session.blocked":"blocked","session.tag":"tag","editor.device":"Smart Charging device (optional \u2014 auto-detected)","editor.title":"Title (optional)","editor.show_flow":"Show source bar & balance","editor.show_controls":"Show controls","editor.show_sessions":"Show sessions & RFID","editor.compact":"Compact (hide controls \u2014 wall dashboards)","editor.hours":"Hours to show (optional)","price.title":"Electricity price","price.no_price":"No price forecast available. Configure a price sensor for {name} first.","price.cheap_threshold":"Cheap below","price.cheap_hours":"{hours} cheap upcoming","price.next_window":"next {start}\u2013{end}","price.no_cheap":"No cheap hours coming up at this threshold","price.now":"now","price.tomorrow":"Tomorrow"},ue={"card.no_device":"Kein {name}-Ger\xE4t gefunden. Richte zuerst eines ein und f\xFCge dann diese Karte hinzu.","card.default_title":"Intelligentes Laden","live.live":"live","live.updated_ago":"vor {ago} aktualisiert","hero.not_connected":"Nicht verbunden","hero.paused":"Pausiert","hero.paused_ready":"Pausiert \xB7 bereit auf {phases} \u03C6","hero.asked_takes":"angefordert {asked} A, Auto nimmt {takes} A","hero.solar_share":"{pct} % Solar","source.solar":"Solar","source.battery":"Batterie","source.grid":"Netz","source.to_car":"{source} \u2192 Auto: {watts} von {total}","source.none":"Aus {source} flie\xDFt gerade nichts.","source.tap_hint":"Segment antippen f\xFCr exakte Watt.","source.exporting":"Haus l\xE4uft auf PV \u2014 \xDCberschuss wird eingespeist.","source.paused":"Auto pausiert \u2014 kein Fluss.","balance.pv":"PV","balance.house":"Haus","balance.grid":"Netz","balance.export":"Einspeisung","balance.battery":"Batterie","balance.idle":"inaktiv","chip.hold":"Batterieentladung gesperrt","chip.hold_manual":"Entladung gesperrt (manuell)","chip.price_cheap":"{price} {unit} \u2014 g\xFCnstig \u2713","chip.price_wait":"{price} {unit} \u2014 warten auf \u2264 {target}","chip.resume_in":"Fortsetzen in {time}","chip.riding_out":"\xDCberbr\xFCcke Einbruch \xB7 {time}","chip.phases":"{phases} \u03C6","chip.forced_off":"Wallbox zwangsweise aus","plan.now":"jetzt","plan.hours_ahead":"+{h} h","plan.drag_hint":"Ziehe die \u2195-Pille, um deine G\xFCnstig-Schwelle zu setzen.","plan.target_aria":"G\xFCnstig-Preis-Ziel, mit Pfeiltasten anpassen","plan.on_track":"im Plan","plan.tight":"knapp \u2014 wenige g\xFCnstige Stunden","control.home_battery":"Hausbatterie","control.mode":"Modus","control.manual_charge":"Jetzt laden","control.manual_current":"Stromst\xE4rke","control.manual_phases":"Phasen","control.smart_control":"Intelligente Steuerung","control.auto_phase":"Auto-Phase (1\u21943)","control.battery_reserve":"Batterie halten \xFCber","control.target_energy":"Ziel-Energie Auto","control.departure":"Abfahrt","control.max_current":"Max. Strom","control.min_current":"Min. Strom","control.tag":"Tag","live.target":"Ziel","live.surplus":"\xDCberschuss","action.start":"Starten","action.stop":"Stoppen","action.start_charging":"Laden starten","action.stop_charging":"Laden stoppen","action.stop_confirm":"Aktiven Ladevorgang stoppen?","session.none_hint":"Kein aktiver Ladevorgang \u2014 einstecken und einen Tag w\xE4hlen.","reason.smart_disabled":"Intelligente Steuerung deaktiviert","reason.manual_passive":"Manueller Modus \u2014 Wallbox unver\xE4ndert","reason.manual_paused":"Manueller Modus \u2014 pausiert","reason.manual_charging":"Manuelles Laden mit {amps} A","reason.manual_charging_guarded":"Manuelles Laden mit {amps} A (Hausbatterie gesch\xFCtzt)","reason.no_car":"Kein Auto verbunden","reason.fast":"Schnellladen mit {amps} A","reason.cheap_grid":"G\xFCnstiger Netzstrom {price}/kWh \u2264 {threshold} \u2192 volle Leistung","reason.cheap_grid_guarded":"G\xFCnstiger Netzstrom {price}/kWh \u2264 {threshold} \u2192 volle Leistung (Hausbatterie gesch\xFCtzt \u2192 {amps} A)","reason.deadline_plan":"Geplante G\xFCnstig-Stunde zu {price}/kWh \u2014 noch {remaining} kWh bis zur Abfahrt","reason.deadline_plan_guarded":"Geplante G\xFCnstig-Stunde zu {price}/kWh \u2014 noch {remaining} kWh bis zur Abfahrt (Hausbatterie gesch\xFCtzt \u2192 {amps} A)","reason.deadline_urgent":"L\xE4dt jetzt, um das Abfahrtsziel zu erreichen \u2014 noch {remaining} kWh","reason.target_reached":"Abfahrtsziel erreicht \u2014 {delivered} kWh geladen","reason.plan_waiting":"Warten auf eine geplante G\xFCnstig-Stunde","reason.waiting_battery_reserve":"Warten \u2014 Hausbatterie {soc}% < Reserve {reserve}%","reason.waiting_surplus":"Warten auf \xDCberschuss \u2014 {surplus} W < {needed} W ben\xF6tigt","reason.surplus_confirm":"\xDCberschuss {surplus} W \u2014 kurze Best\xE4tigung vor dem Start","reason.surplus_ride_out":"\xDCberschuss eingebrochen \u2014 \xFCberbr\xFCckt mit {amps} A","reason.solar_surplus":"Solar\xFCberschuss {surplus} W \u2192 {amps} A","reason.solar_surplus_phase":"Solar\xFCberschuss {surplus} W \u2192 {amps} A ({phases}-phasig)","reason.solar_surplus_eased":"Solar\xFCberschuss {surplus} W \u2192 {amps} A (Hausbatterie wird entlastet)","reason.solar_min_topup":"Minimum {amps} A (nur {surplus} W \xDCberschuss, Aufstockung aus dem Netz)","session.none":"Kein aktiver Ladevorgang","session.charging":"L\xE4dt: {state}","session.last":"Letzter Ladevorgang: {energy}","session.blocked":"gesperrt","session.tag":"Tag","editor.device":"Smart-Charging-Ger\xE4t (optional \u2014 automatisch erkannt)","editor.title":"Titel (optional)","editor.show_flow":"Quellenbalken & Bilanz anzeigen","editor.show_controls":"Steuerung anzeigen","editor.show_sessions":"Ladevorg\xE4nge & RFID anzeigen","editor.compact":"Kompakt (Steuerung ausblenden \u2014 Wand-Dashboards)","editor.hours":"Anzuzeigende Stunden (optional)","price.title":"Strompreis","price.no_price":"Keine Preisprognose verf\xFCgbar. Richte zuerst einen Preissensor f\xFCr {name} ein.","price.cheap_threshold":"G\xFCnstig unter","price.cheap_hours":"{hours} g\xFCnstig in K\xFCrze","price.next_window":"n\xE4chste {start}\u2013{end}","price.no_cheap":"Bei dieser Schwelle keine g\xFCnstigen Stunden in Sicht","price.now":"jetzt","price.tomorrow":"Morgen"},ge={en:Rt,de:ue};function me(a){let s=(a?.locale?.language||a?.language||"en").toLowerCase().split("-")[0];return ge[s]??Rt}function $(a,s,t={}){let r=me(a)[s]??Rt[s]??s;for(let[i,n]of Object.entries(t))r=r.replace(`{${i}}`,n);return r}var F=class extends w{constructor(){super(...arguments);this._schema=[{name:"device",selector:{device:{integration:C}}},{name:"title",selector:{text:{}}},{type:"grid",name:"",schema:[{name:"show_flow",selector:{boolean:{}}},{name:"show_controls",selector:{boolean:{}}},{name:"show_sessions",selector:{boolean:{}}},{name:"compact",selector:{boolean:{}}}]}];this._label=t=>{switch(t.name){case"device":return $(this.hass,"editor.device");case"title":return $(this.hass,"editor.title");case"show_flow":return $(this.hass,"editor.show_flow");case"show_controls":return $(this.hass,"editor.show_controls");case"show_sessions":return $(this.hass,"editor.show_sessions");case"compact":return $(this.hass,"editor.compact");default:return t.name}}}setConfig(t){this._config=t}render(){return!this.hass||!this._config?u:p`<ha-form
      .hass=${this.hass}
      .data=${this._config}
      .schema=${this._schema}
      .computeLabel=${this._label}
      @value-changed=${this._valueChanged}
    ></ha-form>`}_valueChanged(t){let e={...t.detail.value};this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:e},bubbles:!0,composed:!0}))}};F.styles=T`
    ha-form {
      display: block;
      padding: 8px 0;
    }
  `,f([N({attribute:!1})],F.prototype,"hass",2),f([S()],F.prototype,"_config",2),F=f([O("goe-steve-card-editor")],F);var V=class extends w{constructor(){super(...arguments);this._schema=[{name:"device",selector:{device:{integration:C}}},{name:"title",selector:{text:{}}},{name:"hours",selector:{number:{min:6,max:48,mode:"box",unit_of_measurement:"h"}}}];this._label=t=>{switch(t.name){case"device":return $(this.hass,"editor.device");case"title":return $(this.hass,"editor.title");case"hours":return $(this.hass,"editor.hours");default:return t.name}}}setConfig(t){this._config=t}render(){return!this.hass||!this._config?u:p`<ha-form
      .hass=${this.hass}
      .data=${this._config}
      .schema=${this._schema}
      .computeLabel=${this._label}
      @value-changed=${this._valueChanged}
    ></ha-form>`}_valueChanged(t){let e={...t.detail.value};this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:e},bubbles:!0,composed:!0}))}};V.styles=T`
    ha-form {
      display: block;
      padding: 8px 0;
    }
  `,f([N({attribute:!1})],V.prototype,"hass",2),f([S()],V.prototype,"_config",2),V=f([O("goe-steve-price-card-editor")],V);var _e="go-e + SteVe Smart Charging",G=480,_t=200,v={left:38,right:10,top:12,bottom:24},fe=G-v.left-v.right,Tt=_t-v.top-v.bottom,mt=36e5,D=class extends w{constructor(){super(...arguments);this._dragValue=null;this._dragging=!1;this._cheapCache=null}static getConfigElement(){return document.createElement("goe-steve-price-card-editor")}static getStubConfig(t){return{type:"custom:goe-steve-price-card",device:it(t)[0]?.id}}setConfig(t){this._config={...t}}getCardSize(){return 6}get _entities(){return this.hass?gt(this.hass,this._config?.device):null}_t(t,e={}){return $(this.hass,t,e)}_stateObj(t){return t?this.hass.states[t]:void 0}_deviceName(t){if(!t)return null;let e=this.hass.devices[t];return e?.name_by_user||e?.name||null}_slots(t){let r=(t.attributes.slots??[]).map(i=>({start:Date.parse(i.start??""),price:Number(i.price)})).filter(i=>!Number.isNaN(i.start)&&!Number.isNaN(i.price)).sort((i,n)=>i.start-n.start);return r.map((i,n)=>({start:i.start,end:n+1<r.length?r[n+1].start:i.start+mt,price:i.price}))}_cheap(t,e){let r=this._stateObj(t.cheap_price),i=Number(e.attributes.cheap_price),n=r?Number(r.state):Number.isNaN(i)?.15:i,o=r?.attributes??{};return{obj:r,value:n,min:Number(o.min??0),max:Number(o.max??1),step:Number(o.step??.01),unit:e.attributes.unit??o.unit_of_measurement??""}}render(){if(!this.hass||!this._config)return u;let t=this._entities,e=this._stateObj(t?.price_forecast),r=e?this._slots(e):[],i=this._config.title??this._deviceName(t?.deviceId)??this._t("price.title");if(!e||r.length===0){let[c,l]=this._t("price.no_price").split("{name}");return p`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:cash-clock"></ha-icon>
          <p>${c}<b>${_e}</b>${l??""}</p>
        </div>
      </ha-card>`}let n=this._cheap(t,e),o=this._dragValue??n.value;return p`<ha-card>
      <div class="header">
        <div class="title-row">
          <ha-icon icon="mdi:cash-clock"></ha-icon>
          <span class="title">${i}</span>
        </div>
        <div class="now-price">${this._fmtPrice(Number(e.state),n.unit)}</div>
      </div>
      ${this._renderChart(r,o)}
      ${this._renderPreview(r,o)}
      ${this._renderThresholdInput(n,o)}
    </ha-card>`}_shownSlots(t){let e=Date.now(),r=t.filter(i=>i.end>e);if(r.length===0&&(r=t.slice(-1)),this._config.hours&&this._config.hours>0){let i=e+this._config.hours*mt;r=r.filter(n=>n.start<i)}return r.slice(0,96)}_renderChart(t,e){let r=Date.now(),i=this._shownSlots(t),n=i[0].start,o=i[i.length-1].end,c=i.map(b=>b.price),l=Math.min(...c,e),d=Math.max(...c,e),h=d-l||1,g=l-h*.1,_=d+h*.1,y=b=>v.left+(b-n)/(o-n)*fe,L=b=>v.top+(1-(b-g)/(_-g))*Tt,z=v.top+Tt,A=L(e),J=i.map(b=>{let k=y(b.start),R=y(b.end),ot=L(b.price),Jt=b.price<=e;return H`<rect
        class="bar ${Jt?"cheap":""}"
        x=${k+.5}
        y=${ot}
        width=${Math.max(.5,R-k-1)}
        height=${Math.max(0,z-ot)}
      ></rect>`}),j=[];for(let b of i){let k=new Date(b.start);if(k.getHours()===0&&k.getMinutes()===0&&b.start>n){let R=y(b.start);j.push(H`<line class="day-div" x1=${R} y1=${v.top} x2=${R} y2=${z}></line>`),j.push(H`<text class="day-lbl" x=${R+3} y=${v.top+9}>${this._t("price.tomorrow")}</text>`)}}let at=[];for(let b of i){let k=new Date(b.start);if(k.getHours()%6===0&&k.getMinutes()===0){let R=y(b.start);at.push(H`<text class="x-tick" x=${R} y=${_t-8}>${String(k.getHours()).padStart(2,"0")}</text>`)}}let x=r>=n&&r<=o?y(r):null;return p`<div class="chart">
      <svg
        viewBox="0 0 ${G} ${_t}"
        preserveAspectRatio="none"
        @pointermove=${this._onPointerMove}
        @pointerup=${this._onPointerUp}
        @pointercancel=${this._onPointerUp}
      >
        <!-- y grid: min / threshold / max -->
        <text class="y-tick" x=${v.left-4} y=${L(_)+3}>${this._fmtNum(d)}</text>
        <text class="y-tick" x=${v.left-4} y=${z}>${this._fmtNum(l)}</text>
        ${j}
        ${J}
        ${at}
        ${x!==null?H`<line class="now-line" x1=${x} y1=${v.top} x2=${x} y2=${z}></line>
                 <text class="now-tick" x=${x} y=${v.top-2}>${this._t("price.now")}</text>`:u}
        <!-- threshold line + draggable handle -->
        <line class="thresh" x1=${v.left} y1=${A} x2=${G-v.right} y2=${A}></line>
        <g class="handle" data-handle @pointerdown=${this._onPointerDown}>
          <!-- generous, invisible touch target so fingers can grab the handle -->
          <rect class="handle-hit" x=${G-v.right-68} y=${A-20} width="72" height="40"></rect>
          <rect class="handle-chip" x=${G-v.right-52} y=${A-9} width="52" height="18" rx="4"></rect>
          <text x=${G-v.right-26} y=${A+4}>${this._fmtNum(e)}</text>
        </g>
      </svg>
    </div>`}_onPointerDown(t){let e=this._entities,r=this._stateObj(e?.price_forecast);!e||!r||!e.cheap_price||(this._cheapCache=this._cheap(e,r),this._dragging=!0,t.target.setPointerCapture?.(t.pointerId),t.preventDefault(),this._updateDrag(t))}_onPointerMove(t){this._dragging&&(t.preventDefault(),this._updateDrag(t))}_onPointerUp(){if(!this._dragging)return;this._dragging=!1;let t=this._cheapCache,e=this._dragValue;this._dragValue=null,this._cheapCache=null,t?.obj&&e!==null&&e!==t.value&&this.hass.callService("number","set_value",{entity_id:t.obj.entity_id,value:e})}_updateDrag(t){let e=this._cheapCache;if(!e)return;let r=this.renderRoot.querySelector("svg");if(!r)return;let i=r.getBoundingClientRect(),n=(t.clientY-i.top)/i.height*_t,{yMin:o,yMax:c}=this._yDomain(e),l=1-(n-v.top)/Tt,d=o+l*(c-o);d=Math.min(e.max,Math.max(e.min,d)),e.step>0&&(d=Math.round(d/e.step)*e.step);let h=(String(e.step).split(".")[1]??"").length||2;this._dragValue=Number(d.toFixed(h))}_yDomain(t){let e=this._entities,r=this._stateObj(e?.price_forecast),i=r?this._slots(r):[],n=this._shownSlots(i),o=this._dragValue??t.value,c=n.map(g=>g.price),l=Math.min(...c,o),d=Math.max(...c,o),h=d-l||1;return{yMin:l-h*.1,yMax:d+h*.1}}_renderPreview(t,e){let r=Date.now(),n=t.filter(h=>h.end>r).filter(h=>h.price<=e);if(n.length===0)return p`<div class="preview muted">
        <ha-icon icon="mdi:flash-off"></ha-icon><span>${this._t("price.no_cheap")}</span>
      </div>`;let o=n.reduce((h,g)=>h+(Math.min(g.end,r+48*mt)-Math.max(g.start,r))/mt,0),c=n[0],l=c.end;for(let h=1;h<n.length&&n[h].start===l;h++)l=n[h].end;let d=`${o.toFixed(o<10?1:0)} h`;return p`<div class="preview">
      <ha-icon icon="mdi:flash"></ha-icon>
      <span>${this._t("price.cheap_hours",{hours:d})}</span>
      <span class="sep">·</span>
      <span class="muted"
        >${this._t("price.next_window",{start:this._fmtTime(Math.max(c.start,r)),end:this._fmtTime(l)})}</span
      >
    </div>`}_renderThresholdInput(t,e){return t.obj?p`<div class="threshold-row">
      <span class="thr-label">${this._t("price.cheap_threshold")}</span>
      <span class="thr-input">
        <input
          type="number"
          .value=${String(e)}
          min=${t.min}
          max=${t.max}
          step=${t.step}
          @change=${r=>this._setThreshold(t,r.target.value)}
        />
        ${t.unit?p`<span class="thr-unit">${t.unit}</span>`:u}
      </span>
    </div>`:u}_setThreshold(t,e){let r=Number(e);!t.obj||Number.isNaN(r)||r===t.value||this.hass.callService("number","set_value",{entity_id:t.obj.entity_id,value:r})}_fmtNum(t){return t.toFixed(Math.abs(t)<1?2:1)}_fmtPrice(t,e){return Number.isNaN(t)?"\u2014":`${this._fmtNum(t)}${e?` ${e}`:""}`}_fmtTime(t){return new Date(t).toLocaleTimeString(this.hass?.locale?.language??[],{hour:"2-digit",minute:"2-digit"})}};D.styles=T`
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
  `,f([N({attribute:!1})],D.prototype,"hass",2),f([S()],D.prototype,"_config",2),f([S()],D.prototype,"_dragValue",2),D=f([O("goe-steve-price-card")],D);window.customCards=window.customCards||[];window.customCards.push({type:"goe-steve-price-card",name:"go-e + SteVe Price",description:"Electricity-price forecast with a draggable 'cheap' threshold \u2014 see the curve and set what counts as cheap.",preview:!0,documentationURL:"https://github.com/JustChr/HAgoe_steve"});var be="go-e + SteVe Smart Charging",ve=45,ye=230,$e=a=>{if(a==null||Number.isNaN(a))return"\u2014";let s=Math.abs(a);return s>=1e3?`${(a/1e3).toFixed(s>=1e4?0:1)} kW`:`${Math.round(a)} W`},nt=a=>a==null||Number.isNaN(a)?"\u2014":`${(a/1e3).toFixed(1)} kW`,Mt=a=>{let s=Math.max(0,Math.round(a)),t=Math.floor(s/3600),e=Math.floor(s%3600/60),r=s%60;return(t?`${t}:${String(e).padStart(2,"0")}`:`${e}`)+`:${String(r).padStart(2,"0")}`},m=a=>{let s=Number(a);return Number.isNaN(s)?NaN:s},E=class extends w{constructor(){super(...arguments);this._now=Date.now();this._optimistic=new Map;this._dragTarget=null;this._splitNote=null;this._planDown=t=>{t.target.closest(".thhandle")&&(t.preventDefault(),t.currentTarget.setPointerCapture(t.pointerId),this._dragTarget=this._cheapTarget(this._entities))};this._planMove=t=>{if(this._dragTarget===null)return;let e=t.currentTarget.getBoundingClientRect(),r=this._entities,o=(this._stateObj(r.price_forecast)?.attributes?.slots??[]).map(_=>_.price),c=Math.min(...o,this._dragTarget),d=Math.max(...o,this._dragTarget)-c||1,h=e.bottom-t.clientY,g=c+(h-8)/68*d;this._dragTarget=this._clampTarget(r,g)};this._planUp=()=>{if(this._dragTarget===null)return;let t=this._entities,e=this._stateObj(t.cheap_price);e&&this._setNumber(e,String(this._roundTarget(t,this._dragTarget))),this._dragTarget=null}}static getConfigElement(){return document.createElement("goe-steve-card-editor")}static getStubConfig(t){return{type:"custom:goe-steve-card",device:it(t)[0]?.id}}setConfig(t){this._config={show_flow:!0,show_controls:!0,show_sessions:!0,compact:!1,...t}}getCardSize(){return 8}connectedCallback(){super.connectedCallback(),this._timer=window.setInterval(()=>{this._now=Date.now()},1e3)}disconnectedCallback(){super.disconnectedCallback(),this._timer&&window.clearInterval(this._timer)}get _entities(){return this.hass?gt(this.hass,this._config?.device):null}_t(t,e={}){return $(this.hass,t,e)}render(){if(!this.hass||!this._config)return u;let t=this._entities;if(!t||!t.deviceId)return p`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:ev-station"></ha-icon>
          <p>${this._renderNoDevice()}</p>
        </div>
      </ha-card>`;let e=this._config.title??this._deviceName(t.deviceId)??this._t("card.default_title"),r=this._config.show_controls&&!this._config.compact;return p`<ha-card>
      <div class="hacard">
        ${this._renderHead(t,e)}
        ${this._renderHero(t)}
        ${this._renderWhy(t)}
        ${this._config.show_flow?this._renderSplit(t):u}
        ${this._renderChips(t)}
        ${this._renderPlan(t)}
        ${r?this._renderControls(t):u}
        ${this._config.show_sessions?this._renderSession(t):u}
      </div>
    </ha-card>`}_renderNoDevice(){let[t,e]=this._t("card.no_device").split("{name}");return p`${t}<b>${be}</b>${e??""}`}_renderHead(t,e){let r=this._stateObj(t.status),i=this._isOn(t.controlling),n=this._ageSeconds(r??this._stateObj(t.power_flow)),o=n!==null&&n>ve,c=o?this._t("live.updated_ago",{ago:this._fmtAgo(n)}):this._t("live.live");return p`<div class="c-head">
      <ha-icon class="brain ${i?"":"off"}" icon="mdi:brain"></ha-icon>
      <span class="c-title">${e}</span>
      <span class="livedot ${o?"stale":""}"><i></i>${c}</span>
    </div>`}_renderHero(t){let e=this._stateObj(t.power_flow)?.attributes??{},r=this._stateObj(t.status)?.attributes??{},i=m(e.car_w),n=r.charging===!0||i>50,o=e.car_connected,c=m(e.phases),l=this._sourceShares(e),d=2*Math.PI*44,h=0,g=(A,J)=>{let j=H`<circle
        cx="50" cy="50" r="44" stroke="${J}"
        style="stroke-dasharray:${Math.max(A,0)*d} ${d};
               stroke-dashoffset:${-h*d};
               opacity:${A>0?1:0}"></circle>`;return h+=Math.max(A,0),j},_=l.total>0?Math.round(l.solar/l.total*100):0,y=m(r.target_current_a),L=n&&c>0?i/(c*ye):NaN,z=this._heroSub(o,n,c,y,L,_);return p`<div class="c-hero">
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
      <div class="heroright">
        <div class="power">
          ${Number.isNaN(i)?"\u2014":(i/1e3).toFixed(1)} <small>kW</small>
        </div>
        <div class="herosub">${z}</div>
      </div>
    </div>`}_heroSub(t,e,r,i,n,o){if(t===!1)return this._t("hero.not_connected");if(!e)return r>0?this._t("hero.paused_ready",{phases:String(r)}):this._t("hero.paused");let c=[];return!Number.isNaN(n)&&!Number.isNaN(i)&&Math.abs(i-n)>=1.5?c.push(this._t("hero.asked_takes",{asked:String(Math.round(i)),takes:String(Math.round(n))})):!Number.isNaN(i)&&i>0?c.push(`${Math.round(i)} A`):Number.isNaN(n)||c.push(`${Math.round(n)} A`),r>0&&c.push(`${r} \u03C6`),c.push(this._t("hero.solar_share",{pct:String(o)})),c.join(" \xB7 ")}_renderWhy(t){let e=this._stateObj(t.status);return p`<div class="why">${this._statusReason(e)}</div>`}_renderSplit(t){let e=this._stateObj(t.power_flow)?.attributes??{},r=this._stateObj(t.status)?.attributes??{},i=m(e.car_w),n=r.charging===!0||i>50,o=this._sourceShares(e),c=l=>{let d=o.total>0?o[l]/o.total:0;if(d<=.001)return u;let h=this._t(`source.${l}`);return p`<button
        class="seg-src ${l}"
        style="flex-grow:${Math.max(d*100,.001)}"
        @click=${()=>this._tapSource(l,o[l],i)}
      >
        ${d>.14?`${h} ${Math.round(d*100)} %`:d>.05?`${Math.round(d*100)} %`:""}
      </button>`};return p`<div class="split">
      <div class="splitbar ${n?"flowing":""}">
        ${c("solar")}${c("battery")}${c("grid")}
      </div>
      <div class="splitnote" id="splitnote">
        ${this._splitNote??this._defaultSplitNote(o.total,e)}
      </div>
      ${this._renderBalance(t,e)}
    </div>`}_tapSource(t,e,r){let i=this._t(`source.${t}`);this._splitNote=e>0?this._t("source.to_car",{source:i,watts:$e(e),total:nt(r)}):this._t("source.none",{source:i}),this.requestUpdate()}_defaultSplitNote(t,e){return t>0?this._t("source.tap_hint"):e.car_connected===!1?this._t("source.exporting"):this._t("source.paused")}_renderBalance(t,e){let r=m(e.pv_w),i=m(e.house_w),n=m(e.grid_w),o=e.battery_w===null||e.battery_w===void 0?null:m(e.battery_w),c=e.battery_soc,l=m(this._stateObj(t.battery_reserve_soc)?.state),d=this._holdActive(t),h=[];if(Number.isNaN(r)||h.push(p`<span><i class="dot" style="background:var(--goe-solar)"></i>${this._t("balance.pv")} <b>${nt(r)}</b></span>`),Number.isNaN(i)||h.push(p`<span>${this._t("balance.house")} <b>${nt(i)}</b></span>`),Number.isNaN(n)||h.push(p`<span><i class="dot" style="background:var(--goe-grid)"></i>${n<-50?this._t("balance.export"):this._t("balance.grid")} <b>${nt(Math.abs(n))}</b></span>`),o!==null){let g=o>50?"+ ":o<-50?"\u2212 ":"",_=Math.abs(o)<=50?this._t("balance.idle"):`${g}${nt(Math.abs(o))}`,y=c!=null?` \xB7 ${Math.round(m(c))} %${Number.isNaN(l)?"":` \u25B8 ${Math.round(l)} %`}${d?" \u{1F6E1}":""}`:"";h.push(p`<span><i class="dot" style="background:var(--goe-battery)"></i>${this._t("balance.battery")} <b>${_}</b>${y}</span>`)}return p`<div class="balance">${h}</div>`}_renderChips(t){let e=this._stateObj(t.status)?.attributes??{},r=[];if(this._holdActive(t)){let l=(e.hold_source??"auto")==="hold";r.push(this._chip("mdi:shield",l?"chip.hold_manual":"chip.hold",{},"hold"))}let i=this._stateObj(t.price_forecast);if(i&&!["unknown","unavailable",""].includes(i.state)){let l=m(i.state),d=this._cheapTarget(t),h=i.attributes.unit??"";if(!Number.isNaN(l)){let g=!Number.isNaN(d)&&l<=d;r.push(this._chip("mdi:cash-clock",g?"chip.price_cheap":"chip.price_wait",{price:this._fmtPriceNum(l),unit:h,target:this._fmtPriceNum(d)},g?"cheap":""))}}let n=this._countdown(e.resume_not_before);n!==null&&r.push(this._chip("mdi:clock-outline","chip.resume_in",{time:Mt(n)}));let o=this._countdown(e.pause_not_before);o!==null&&r.push(this._chip("mdi:clock-outline","chip.riding_out",{time:Mt(o)}));let c=m((this._stateObj(t.power_flow)?.attributes??{}).phases);return!Number.isNaN(c)&&c>0&&r.push(this._chip("mdi:sine-wave","chip.phases",{phases:String(c)})),e.forced===!1&&r.push(this._chip("mdi:hand-back-left","chip.forced_off",{},"hold")),r.length===0?p``:p`<div class="chips">${r}</div>`}_chip(t,e,r,i=""){return p`<span class="chipx ${i}"><ha-icon icon="${t}"></ha-icon>${this._t(e,r)}</span>`}_renderPlan(t){if(this._effectiveState(t.charging_mode)!=="smart")return u;let r=this._stateObj(t.price_forecast),i=r?.attributes?.slots??[];if(i.length<2)return u;let n=this._stateObj(t.status)?.attributes??{},o=new Set(n.plan??[]),c=this._dragTarget??this._cheapTarget(t),l=i.map(x=>x.price),d=Math.min(...l,c),g=Math.max(...l,c)-d||1,_=x=>8+(x-d)/g*68,y=this._now,L=this._nowSlotIndex(i,y),z=i.map((x,b)=>{let k=o.has(x.start),R=x.price<=c,ot="pb"+(b===L?" now":"")+(k?" win":R?" cheap":"");return p`<i class="${ot}" style="height:${_(x.price)}px"></i>`}),A=r?.attributes?.unit??"",J=`\u2195 \u2264 ${this._fmtPriceNum(c)} ${A}`,j=this._t("plan.hours_ahead",{h:String(i.length-1)}),at=this._planLine(t,o.size);return p`<div class="plan">
      <div
        class="planbars"
        @pointerdown=${this._planDown}
        @pointermove=${this._planMove}
        @pointerup=${this._planUp}
        @pointercancel=${this._planUp}
      >
        ${z}
        <span class="thline" style="bottom:${_(c)}px">
          <button
            class="thhandle"
            aria-label=${this._t("plan.target_aria")}
            @keydown=${x=>this._planKey(t,x)}
          >${J}</button>
        </span>
      </div>
      <div class="planaxis"><span>${this._t("plan.now")}</span><span>${j}</span></div>
      <div class="planhint">${this._t("plan.drag_hint")}</div>
      ${at}
    </div>`}_planLine(t,e){let r=m(this._stateObj(t.target_energy)?.state);if(Number.isNaN(r)||r<=0)return u;let i=m((this._stateObj(t.power_flow)?.attributes??{}).session_energy_kwh),n=Number.isNaN(i)?0:i,o=Math.min(100,Math.round(n/r*100)),c=e>=4?this._t("plan.on_track"):this._t("plan.tight");return p`
      <div class="planline">
        <b>${n.toFixed(1)} / ${r.toFixed(0)} kWh</b> — ${c}
      </div>
      <div class="progress"><i style="width:${o}%"></i></div>`}_nowSlotIndex(t,e){let r=0;for(let i=0;i<t.length&&Date.parse(t[i].start)<=e;i++)r=i;return r}_planKey(t,e){if(e.key!=="ArrowUp"&&e.key!=="ArrowDown")return;e.preventDefault();let r=this._stateObj(t.cheap_price);if(!r)return;let i=m(r.attributes.step)||.01,n=this._cheapTarget(t),o=this._clampTarget(t,n+(e.key==="ArrowUp"?i:-i));this._setNumber(r,String(this._roundTarget(t,o)))}_clampTarget(t,e){let r=this._stateObj(t.cheap_price),i=m(r?.attributes.min),n=m(r?.attributes.max);return Number.isNaN(i)||(e=Math.max(i,e)),Number.isNaN(n)||(e=Math.min(n,e)),e}_roundTarget(t,e){let r=m(this._stateObj(t.cheap_price)?.attributes.step)||.01;return Math.round(e/r)*r}_renderControls(t){let e=this._stateObj(t.charging_mode),r=this._effectiveState(t.charging_mode),i=r==="manual";return p`<div class="controls">
      ${e?this._renderModeSeg(t,e):u}
      <div class="ctxctl">
        ${i?this._renderManual(t):this._renderModeTunables(t,r)}
        ${this._renderBatteryThreeWay(t)}
        ${this._renderNumberRow(t.battery_reserve_soc,"control.battery_reserve")}
      </div>
    </div>`}_renderModeSeg(t,e){let r=e.attributes.options??[],i=this._effectiveState(t.charging_mode),n={manual:"mdi:hand-back-right",solar:"mdi:solar-power",solar_min:"mdi:solar-power-variant",smart:"mdi:brain",fast:"mdi:flash"};return p`<div class="seg">
      ${r.map(o=>p`<button
          class="${o===i?"on":""}"
          @click=${()=>this._selectOptimistic(e,o)}
        >
          <ha-icon icon="${n[o]??"mdi:ev-station"}"></ha-icon>
          <span>${this._localizeOption(e,o)}</span>
        </button>`)}
    </div>`}_renderModeTunables(t,e){return p`
      ${e==="smart"?p`${this._renderNumberRow(t.target_energy,"control.target_energy")}
            ${this._renderDateTimeRow(t.departure,"control.departure")}`:u}
      ${e==="solar_min"?this._renderNumberRow(t.min_current,"control.min_current"):u}
      ${e==="fast"?this._renderNumberRow(t.max_current,"control.max_current"):u}
      ${t.auto_phase?p`<div class="ctlrow">
            <label>${this._t("control.auto_phase")}</label>
            <ha-switch
              .checked=${this._isOn(t.auto_phase)}
              @change=${r=>this._toggle(t.auto_phase,r)}
            ></ha-switch>
          </div>`:u}`}_renderManual(t){let e=this._isOn(t.manual_charge);return p`
      ${t.manual_charge?p`<button
            class="bigbtn ${e?"stop":""}"
            @click=${()=>this._toggleManualCharge(t,e)}
          >
            <ha-icon icon="${e?"mdi:stop":"mdi:play"}"></ha-icon>
            ${e?this._t("action.stop_charging"):this._t("action.start_charging")}
          </button>`:u}
      ${this._renderNumberRow(t.manual_current,"control.manual_current")}
      ${t.manual_phases?p`<div class="ctlrow">
            <label>${this._t("control.manual_phases")}</label>
            ${this._renderSelect(this._stateObj(t.manual_phases))}
          </div>`:u}`}_renderBatteryThreeWay(t){let e=this._stateObj(t.battery_hold_mode);if(!e)return u;let r=e.attributes.options??["auto","hold","free"],i=this._effectiveState(t.battery_hold_mode),n=this._holdActive(t);return p`<div class="ctlrow">
      <label>${this._t("control.home_battery")}</label>
      <span class="minisg">
        ${r.map(o=>p`<button
            class="${o===i?"on":""}"
            @click=${()=>this._selectOptimistic(e,o)}
          >
            ${this._localizeOption(e,o)}${o==="auto"&&n&&i==="auto"?" \u{1F6E1}":""}
          </button>`)}
      </span>
    </div>`}_renderNumberRow(t,e){let r=this._stateObj(t);return r?p`<div class="ctlrow">
      <label>${this._t(e)}</label>
      ${this._renderNumber(r)}
    </div>`:u}_renderDateTimeRow(t,e){let r=this._stateObj(t);return r?p`<div class="ctlrow">
      <label>${this._t(e)}</label>
      ${this._renderDateTime(r)}
    </div>`:u}_renderSession(t){let e=this._stateObj(t.active_transaction),r=this._stateObj(t.selected_tag);if(!e&&!r)return u;let i=!!e&&!["idle","unknown","unavailable",""].includes(e.state),n=this._stateObj(t.power_flow)?.attributes??{},o=m(n.session_energy_kwh),c="";if(i&&e){let l=e.attributes.name??e.state,d=this._liveDuration(e.attributes.started),h=[];d&&h.push(d),!Number.isNaN(o)&&o>0&&h.push(`${o.toFixed(2)} kWh`),c=p`<b>${l}</b>${h.length?p` · <span class="mono">${h.join(" \xB7 ")}</span>`:u}`}return p`<div class="session">
      ${this._renderTagPicker(r,i)}
      <div class="session-row">
        <ha-icon icon="mdi:card-account-details"></ha-icon>
        <span>${i?c:this._t("session.none_hint")}</span>
      </div>
    </div>`}_renderTagPicker(t,e){if(!t)return u;let r=t.attributes.options??[];if(r.length===0)return u;let i=r.includes(t.state);return p`<div class="tag-picker">
      ${e?u:p`<div class="ctlrow">
            <label>${this._t("control.tag")}</label>
            ${this._renderSelect(t)}
          </div>`}
      <div class="tag-actions">
        ${e?p`<button class="bigbtn stop" @click=${()=>this._confirmStop()}>
              <ha-icon icon="mdi:stop"></ha-icon>${this._t("action.stop")}
            </button>`:p`<button
              class="bigbtn"
              ?disabled=${!i}
              @click=${()=>this._callTagService("remote_start")}
            >
              <ha-icon icon="mdi:play"></ha-icon>${this._t("action.start")}
            </button>`}
      </div>
    </div>`}_statusReason(t){let e=t?.state&&t.state!=="unknown"?t.state:"\u2014",r=t?.attributes?.reason_key;if(!r)return e;let i=`reason.${r}`,n=t?.attributes?.reason_params??{},o=this._t(i,this._localizeNumbers(n));return o===i?e:o}_localizeNumbers(t){let e=(this.hass?.locale?.language||this.hass?.language||"en").toLowerCase().split("-")[0],r={};for(let[i,n]of Object.entries(t)){let o=/^-?\d+(?:\.(\d+))?$/.exec(n);if(o){let c=o[1]?.length??0;r[i]=new Intl.NumberFormat(e,{minimumFractionDigits:c,maximumFractionDigits:c}).format(Number(n))}else r[i]=n}return r}_renderNumber(t){let e=t.attributes,r=e.unit_of_measurement??"";return p`<span class="ctl-number-wrap">
      <input
        class="ctl-number"
        type="number"
        .value=${t.state}
        min=${e.min??u}
        max=${e.max??u}
        step=${e.step??u}
        @change=${i=>this._setNumber(t,i.target.value)}
      />
      ${r?p`<span class="ctl-unit">${r}</span>`:u}
    </span>`}_setNumber(t,e){let r=Number(e);Number.isNaN(r)||String(r)===t.state||this.hass.callService("number","set_value",{entity_id:t.entity_id,value:r})}_renderDateTime(t){return p`<input
      class="ctl-datetime"
      type="datetime-local"
      .value=${this._toLocalInput(t.state)}
      @change=${e=>this._setDateTime(t,e.target.value)}
    />`}_toLocalInput(t){let e=new Date(t);if(Number.isNaN(e.getTime()))return"";let r=i=>String(i).padStart(2,"0");return`${e.getFullYear()}-${r(e.getMonth()+1)}-${r(e.getDate())}T${r(e.getHours())}:${r(e.getMinutes())}`}_setDateTime(t,e){if(!e)return;let r=new Date(e);Number.isNaN(r.getTime())||this.hass.callService("datetime","set_value",{entity_id:t.entity_id,datetime:r.toISOString()})}_renderSelect(t){let e=t.attributes.options??[];return p`<select
      class="ctl-select"
      @change=${r=>this._selectOption(t,r.target.value)}
    >
      ${e.map(r=>p`<option .value=${r} ?selected=${r===t.state}>
          ${this._localizeOption(t,r)}
        </option>`)}
    </select>`}_callTagService(t){this.hass.callService(C,t,{})}_confirmStop(){window.confirm(this._t("action.stop_confirm"))&&this._callTagService("remote_stop")}_toggleManualCharge(t,e){t.manual_charge&&this.hass.callService("switch",e?"turn_off":"turn_on",{entity_id:t.manual_charge})}_sourceShares(t){let e=t.sources??{},r=Math.max(0,m(e.solar_w)||0),i=Math.max(0,m(e.battery_w)||0),n=Math.max(0,m(e.grid_w)||0);return{solar:r,battery:i,grid:n,total:r+i+n}}_cheapTarget(t){if(this._dragTarget!==null)return this._dragTarget;let e=this._stateObj(t.price_forecast),r=m(e?.attributes?.cheap_price);return Number.isNaN(r)?m(this._stateObj(t.cheap_price)?.state):r}_holdActive(t){let e=(this._stateObj(t.status)?.attributes??{}).hold_battery;return typeof e=="boolean"?e:this._isOn(t.battery_hold)}_countdown(t){if(typeof t!="string")return null;let e=Date.parse(t);if(Number.isNaN(e))return null;let r=(e-this._now)/1e3;return r>0?r:null}_ageSeconds(t){if(!t?.last_updated)return null;let e=Date.parse(t.last_updated);return Number.isNaN(e)?null:Math.max(0,(this._now-e)/1e3)}_fmtAgo(t){return t<90?`${Math.round(t)} s`:`${Math.round(t/60)} min`}_liveDuration(t){if(!t)return"";let e=Date.parse(t);return Number.isNaN(e)?"":Mt((this._now-e)/1e3)}_fmtPriceNum(t){return Number.isNaN(t)?"\u2014":Number.isInteger(t)?String(t):t.toFixed(t<1?2:1)}_effectiveState(t){let e=this._stateObj(t)?.state;if(!t)return e;let r=this._optimistic.get(t);return r?e===r.value||Date.now()-r.at>4e3?(this._optimistic.delete(t),e):r.value:e}_selectOptimistic(t,e){e!==t.state&&(this._optimistic.set(t.entity_id,{value:e,at:Date.now()}),this.requestUpdate(),this.hass.callService("select","select_option",{entity_id:t.entity_id,option:e}))}_stateObj(t){return t?this.hass.states[t]:void 0}_isOn(t){return this._stateObj(t)?.state==="on"}_localizeOption(t,e){let r=this.hass.entities?.[t.entity_id]?.translation_key;if(r){let i=`component.${C}.entity.select.${r}.state.${e}`,n=this.hass.localize?.(i);if(n)return n}if(this.hass.formatEntityState){let i=this.hass.formatEntityState({...t,state:e},e);if(i)return i}return e}_deviceName(t){let e=this.hass.devices[t];return e?.name_by_user||e?.name||null}_selectOption(t,e){e!==t.state&&this.hass.callService("select","select_option",{entity_id:t.entity_id,option:e})}_toggle(t,e){if(!t)return;let r=e.target.checked;this.hass.callService("switch",r?"turn_on":"turn_off",{entity_id:t})}};E.styles=T`
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
    .ring {
      width: 92px;
      height: 92px;
      flex: none;
      position: relative;
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

    /* Plan strip */
    .planbars {
      display: flex;
      align-items: flex-end;
      gap: 2px;
      height: 76px;
      position: relative;
      touch-action: pan-y;
    }
    .pb {
      flex: 1;
      border-radius: 3px 3px 0 0;
      background: var(--goe-chip);
      position: relative;
    }
    .pb.cheap {
      background: color-mix(in srgb, var(--goe-accent) 30%, var(--goe-chip));
    }
    .pb.win {
      background: var(--goe-accent);
    }
    .pb.now::after {
      content: "";
      position: absolute;
      inset: -3px auto -3px 50%;
      border-left: 2px solid var(--primary-text-color);
      opacity: 0.7;
    }
    .thline {
      position: absolute;
      left: 0;
      right: 0;
      border-top: 1.5px dashed var(--goe-accent);
      pointer-events: none;
    }
    .thhandle {
      position: absolute;
      right: 0;
      bottom: 2px;
      pointer-events: auto;
      font-size: 0.66rem;
      font-weight: 600;
      color: var(--goe-accent);
      background: var(--card-background-color);
      border: 1px solid var(--goe-accent);
      border-radius: 999px;
      padding: 3px 10px;
      cursor: ns-resize;
      font-variant-numeric: tabular-nums;
      white-space: nowrap;
      touch-action: none;
      font-family: inherit;
    }
    .planaxis {
      display: flex;
      justify-content: space-between;
      font-size: 0.68rem;
      color: var(--secondary-text-color);
      margin-top: 4px;
      font-variant-numeric: tabular-nums;
    }
    .planhint {
      font-size: 0.68rem;
      color: var(--secondary-text-color);
      margin-top: 4px;
      font-style: italic;
    }
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
    :focus-visible {
      outline: 2px solid var(--goe-accent);
      outline-offset: 2px;
    }
  `,f([N({attribute:!1})],E.prototype,"hass",2),f([S()],E.prototype,"_config",2),f([S()],E.prototype,"_now",2),f([S()],E.prototype,"_optimistic",2),f([S()],E.prototype,"_dragTarget",2),E=f([O("goe-steve-card")],E);window.customCards=window.customCards||[];window.customCards.push({type:"goe-steve-card",name:"go-e + SteVe Smart Charging",description:"Live source split, the brain's reasoning, plan strip and inline controls for smart EV charging.",preview:!0,documentationURL:"https://github.com/JustChr/HAgoe_steve"});export{E as GoeSteveCard};
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
