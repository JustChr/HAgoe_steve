/* go-e + SteVe Smart Charging card — bundled, do not edit by hand. Source in /card. */
var Pt=Object.defineProperty;var Tt=Object.getOwnPropertyDescriptor;var v=(r,t,e,s)=>{for(var i=s>1?void 0:s?Tt(t,e):t,n=r.length-1,o;n>=0;n--)(o=r[n])&&(i=(s?o(t,e,i):o(i))||i);return s&&i&&Pt(t,e,i),i};var B=globalThis,F=B.ShadowRoot&&(B.ShadyCSS===void 0||B.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,tt=Symbol(),ft=new WeakMap,H=class{constructor(t,e,s){if(this._$cssResult$=!0,s!==tt)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=t,this.t=e}get styleSheet(){let t=this.o,e=this.t;if(F&&t===void 0){let s=e!==void 0&&e.length===1;s&&(t=ft.get(e)),t===void 0&&((this.o=t=new CSSStyleSheet).replaceSync(this.cssText),s&&ft.set(e,t))}return t}toString(){return this.cssText}},mt=r=>new H(typeof r=="string"?r:r+"",void 0,tt),P=(r,...t)=>{let e=r.length===1?r[0]:t.reduce((s,i,n)=>s+(o=>{if(o._$cssResult$===!0)return o.cssText;if(typeof o=="number")return o;throw Error("Value passed to 'css' function must be a 'css' function result: "+o+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(i)+r[n+1],r[0]);return new H(e,r,tt)},_t=(r,t)=>{if(F)r.adoptedStyleSheets=t.map(e=>e instanceof CSSStyleSheet?e:e.styleSheet);else for(let e of t){let s=document.createElement("style"),i=B.litNonce;i!==void 0&&s.setAttribute("nonce",i),s.textContent=e.cssText,r.appendChild(s)}},et=F?r=>r:r=>r instanceof CSSStyleSheet?(t=>{let e="";for(let s of t.cssRules)e+=s.cssText;return mt(e)})(r):r;var{is:Lt,defineProperty:Ut,getOwnPropertyDescriptor:zt,getOwnPropertyNames:jt,getOwnPropertySymbols:Dt,getPrototypeOf:It}=Object,V=globalThis,yt=V.trustedTypes,qt=yt?yt.emptyScript:"",Bt=V.reactiveElementPolyfillSupport,T=(r,t)=>r,L={toAttribute(r,t){switch(t){case Boolean:r=r?qt:null;break;case Object:case Array:r=r==null?r:JSON.stringify(r)}return r},fromAttribute(r,t){let e=r;switch(t){case Boolean:e=r!==null;break;case Number:e=r===null?null:Number(r);break;case Object:case Array:try{e=JSON.parse(r)}catch{e=null}}return e}},W=(r,t)=>!Lt(r,t),vt={attribute:!0,type:String,converter:L,reflect:!1,useDefault:!1,hasChanged:W};Symbol.metadata??=Symbol("metadata"),V.litPropertyMetadata??=new WeakMap;var y=class extends HTMLElement{static addInitializer(t){this._$Ei(),(this.l??=[]).push(t)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(t,e=vt){if(e.state&&(e.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(t)&&((e=Object.create(e)).wrapped=!0),this.elementProperties.set(t,e),!e.noAccessor){let s=Symbol(),i=this.getPropertyDescriptor(t,s,e);i!==void 0&&Ut(this.prototype,t,i)}}static getPropertyDescriptor(t,e,s){let{get:i,set:n}=zt(this.prototype,t)??{get(){return this[e]},set(o){this[e]=o}};return{get:i,set(o){let l=i?.call(this);n?.call(this,o),this.requestUpdate(t,l,s)},configurable:!0,enumerable:!0}}static getPropertyOptions(t){return this.elementProperties.get(t)??vt}static _$Ei(){if(this.hasOwnProperty(T("elementProperties")))return;let t=It(this);t.finalize(),t.l!==void 0&&(this.l=[...t.l]),this.elementProperties=new Map(t.elementProperties)}static finalize(){if(this.hasOwnProperty(T("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(T("properties"))){let e=this.properties,s=[...jt(e),...Dt(e)];for(let i of s)this.createProperty(i,e[i])}let t=this[Symbol.metadata];if(t!==null){let e=litPropertyMetadata.get(t);if(e!==void 0)for(let[s,i]of e)this.elementProperties.set(s,i)}this._$Eh=new Map;for(let[e,s]of this.elementProperties){let i=this._$Eu(e,s);i!==void 0&&this._$Eh.set(i,e)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(t){let e=[];if(Array.isArray(t)){let s=new Set(t.flat(1/0).reverse());for(let i of s)e.unshift(et(i))}else t!==void 0&&e.push(et(t));return e}static _$Eu(t,e){let s=e.attribute;return s===!1?void 0:typeof s=="string"?s:typeof t=="string"?t.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(t=>this.enableUpdating=t),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(t=>t(this))}addController(t){(this._$EO??=new Set).add(t),this.renderRoot!==void 0&&this.isConnected&&t.hostConnected?.()}removeController(t){this._$EO?.delete(t)}_$E_(){let t=new Map,e=this.constructor.elementProperties;for(let s of e.keys())this.hasOwnProperty(s)&&(t.set(s,this[s]),delete this[s]);t.size>0&&(this._$Ep=t)}createRenderRoot(){let t=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return _t(t,this.constructor.elementStyles),t}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(t=>t.hostConnected?.())}enableUpdating(t){}disconnectedCallback(){this._$EO?.forEach(t=>t.hostDisconnected?.())}attributeChangedCallback(t,e,s){this._$AK(t,s)}_$ET(t,e){let s=this.constructor.elementProperties.get(t),i=this.constructor._$Eu(t,s);if(i!==void 0&&s.reflect===!0){let n=(s.converter?.toAttribute!==void 0?s.converter:L).toAttribute(e,s.type);this._$Em=t,n==null?this.removeAttribute(i):this.setAttribute(i,n),this._$Em=null}}_$AK(t,e){let s=this.constructor,i=s._$Eh.get(t);if(i!==void 0&&this._$Em!==i){let n=s.getPropertyOptions(i),o=typeof n.converter=="function"?{fromAttribute:n.converter}:n.converter?.fromAttribute!==void 0?n.converter:L;this._$Em=i;let l=o.fromAttribute(e,n.type);this[i]=l??this._$Ej?.get(i)??l,this._$Em=null}}requestUpdate(t,e,s,i=!1,n){if(t!==void 0){let o=this.constructor;if(i===!1&&(n=this[t]),s??=o.getPropertyOptions(t),!((s.hasChanged??W)(n,e)||s.useDefault&&s.reflect&&n===this._$Ej?.get(t)&&!this.hasAttribute(o._$Eu(t,s))))return;this.C(t,e,s)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(t,e,{useDefault:s,reflect:i,wrapped:n},o){s&&!(this._$Ej??=new Map).has(t)&&(this._$Ej.set(t,o??e??this[t]),n!==!0||o!==void 0)||(this._$AL.has(t)||(this.hasUpdated||s||(e=void 0),this._$AL.set(t,e)),i===!0&&this._$Em!==t&&(this._$Eq??=new Set).add(t))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(e){Promise.reject(e)}let t=this.scheduleUpdate();return t!=null&&await t,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(let[i,n]of this._$Ep)this[i]=n;this._$Ep=void 0}let s=this.constructor.elementProperties;if(s.size>0)for(let[i,n]of s){let{wrapped:o}=n,l=this[i];o!==!0||this._$AL.has(i)||l===void 0||this.C(i,void 0,n,l)}}let t=!1,e=this._$AL;try{t=this.shouldUpdate(e),t?(this.willUpdate(e),this._$EO?.forEach(s=>s.hostUpdate?.()),this.update(e)):this._$EM()}catch(s){throw t=!1,this._$EM(),s}t&&this._$AE(e)}willUpdate(t){}_$AE(t){this._$EO?.forEach(e=>e.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(t)),this.updated(t)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(t){return!0}update(t){this._$Eq&&=this._$Eq.forEach(e=>this._$ET(e,this[e])),this._$EM()}updated(t){}firstUpdated(t){}};y.elementStyles=[],y.shadowRootOptions={mode:"open"},y[T("elementProperties")]=new Map,y[T("finalized")]=new Map,Bt?.({ReactiveElement:y}),(V.reactiveElementVersions??=[]).push("2.1.2");var lt=globalThis,$t=r=>r,K=lt.trustedTypes,bt=K?K.createPolicy("lit-html",{createHTML:r=>r}):void 0,Ct="$lit$",$=`lit$${Math.random().toFixed(9).slice(2)}$`,Rt="?"+$,Ft=`<${Rt}>`,A=document,z=()=>A.createComment(""),j=r=>r===null||typeof r!="object"&&typeof r!="function",ct=Array.isArray,Vt=r=>ct(r)||typeof r?.[Symbol.iterator]=="function",st=`[ 	
\f\r]`,U=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,wt=/-->/g,xt=/>/g,w=RegExp(`>|${st}(?:([^\\s"'>=/]+)(${st}*=${st}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),At=/'/g,Et=/"/g,kt=/^(?:script|style|textarea|title)$/i,ht=r=>(t,...e)=>({_$litType$:r,strings:t,values:e}),p=ht(1),dt=ht(2),oe=ht(3),E=Symbol.for("lit-noChange"),c=Symbol.for("lit-nothing"),St=new WeakMap,x=A.createTreeWalker(A,129);function Nt(r,t){if(!ct(r)||!r.hasOwnProperty("raw"))throw Error("invalid template strings array");return bt!==void 0?bt.createHTML(t):t}var Wt=(r,t)=>{let e=r.length-1,s=[],i,n=t===2?"<svg>":t===3?"<math>":"",o=U;for(let l=0;l<e;l++){let a=r[l],d,u,h=-1,g=0;for(;g<a.length&&(o.lastIndex=g,u=o.exec(a),u!==null);)g=o.lastIndex,o===U?u[1]==="!--"?o=wt:u[1]!==void 0?o=xt:u[2]!==void 0?(kt.test(u[2])&&(i=RegExp("</"+u[2],"g")),o=w):u[3]!==void 0&&(o=w):o===w?u[0]===">"?(o=i??U,h=-1):u[1]===void 0?h=-2:(h=o.lastIndex-u[2].length,d=u[1],o=u[3]===void 0?w:u[3]==='"'?Et:At):o===Et||o===At?o=w:o===wt||o===xt?o=U:(o=w,i=void 0);let f=o===w&&r[l+1].startsWith("/>")?" ":"";n+=o===U?a+Ft:h>=0?(s.push(d),a.slice(0,h)+Ct+a.slice(h)+$+f):a+$+(h===-2?l:f)}return[Nt(r,n+(r[e]||"<?>")+(t===2?"</svg>":t===3?"</math>":"")),s]},D=class r{constructor({strings:t,_$litType$:e},s){let i;this.parts=[];let n=0,o=0,l=t.length-1,a=this.parts,[d,u]=Wt(t,e);if(this.el=r.createElement(d,s),x.currentNode=this.el.content,e===2||e===3){let h=this.el.content.firstChild;h.replaceWith(...h.childNodes)}for(;(i=x.nextNode())!==null&&a.length<l;){if(i.nodeType===1){if(i.hasAttributes())for(let h of i.getAttributeNames())if(h.endsWith(Ct)){let g=u[o++],f=i.getAttribute(h).split($),_=/([.?@])?(.*)/.exec(g);a.push({type:1,index:n,name:_[2],strings:f,ctor:_[1]==="."?rt:_[1]==="?"?nt:_[1]==="@"?ot:k}),i.removeAttribute(h)}else h.startsWith($)&&(a.push({type:6,index:n}),i.removeAttribute(h));if(kt.test(i.tagName)){let h=i.textContent.split($),g=h.length-1;if(g>0){i.textContent=K?K.emptyScript:"";for(let f=0;f<g;f++)i.append(h[f],z()),x.nextNode(),a.push({type:2,index:++n});i.append(h[g],z())}}}else if(i.nodeType===8)if(i.data===Rt)a.push({type:2,index:n});else{let h=-1;for(;(h=i.data.indexOf($,h+1))!==-1;)a.push({type:7,index:n}),h+=$.length-1}n++}}static createElement(t,e){let s=A.createElement("template");return s.innerHTML=t,s}};function R(r,t,e=r,s){if(t===E)return t;let i=s!==void 0?e._$Co?.[s]:e._$Cl,n=j(t)?void 0:t._$litDirective$;return i?.constructor!==n&&(i?._$AO?.(!1),n===void 0?i=void 0:(i=new n(r),i._$AT(r,e,s)),s!==void 0?(e._$Co??=[])[s]=i:e._$Cl=i),i!==void 0&&(t=R(r,i._$AS(r,t.values),i,s)),t}var it=class{constructor(t,e){this._$AV=[],this._$AN=void 0,this._$AD=t,this._$AM=e}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(t){let{el:{content:e},parts:s}=this._$AD,i=(t?.creationScope??A).importNode(e,!0);x.currentNode=i;let n=x.nextNode(),o=0,l=0,a=s[0];for(;a!==void 0;){if(o===a.index){let d;a.type===2?d=new I(n,n.nextSibling,this,t):a.type===1?d=new a.ctor(n,a.name,a.strings,this,t):a.type===6&&(d=new at(n,this,t)),this._$AV.push(d),a=s[++l]}o!==a?.index&&(n=x.nextNode(),o++)}return x.currentNode=A,i}p(t){let e=0;for(let s of this._$AV)s!==void 0&&(s.strings!==void 0?(s._$AI(t,s,e),e+=s.strings.length-2):s._$AI(t[e])),e++}},I=class r{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(t,e,s,i){this.type=2,this._$AH=c,this._$AN=void 0,this._$AA=t,this._$AB=e,this._$AM=s,this.options=i,this._$Cv=i?.isConnected??!0}get parentNode(){let t=this._$AA.parentNode,e=this._$AM;return e!==void 0&&t?.nodeType===11&&(t=e.parentNode),t}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(t,e=this){t=R(this,t,e),j(t)?t===c||t==null||t===""?(this._$AH!==c&&this._$AR(),this._$AH=c):t!==this._$AH&&t!==E&&this._(t):t._$litType$!==void 0?this.$(t):t.nodeType!==void 0?this.T(t):Vt(t)?this.k(t):this._(t)}O(t){return this._$AA.parentNode.insertBefore(t,this._$AB)}T(t){this._$AH!==t&&(this._$AR(),this._$AH=this.O(t))}_(t){this._$AH!==c&&j(this._$AH)?this._$AA.nextSibling.data=t:this.T(A.createTextNode(t)),this._$AH=t}$(t){let{values:e,_$litType$:s}=t,i=typeof s=="number"?this._$AC(t):(s.el===void 0&&(s.el=D.createElement(Nt(s.h,s.h[0]),this.options)),s);if(this._$AH?._$AD===i)this._$AH.p(e);else{let n=new it(i,this),o=n.u(this.options);n.p(e),this.T(o),this._$AH=n}}_$AC(t){let e=St.get(t.strings);return e===void 0&&St.set(t.strings,e=new D(t)),e}k(t){ct(this._$AH)||(this._$AH=[],this._$AR());let e=this._$AH,s,i=0;for(let n of t)i===e.length?e.push(s=new r(this.O(z()),this.O(z()),this,this.options)):s=e[i],s._$AI(n),i++;i<e.length&&(this._$AR(s&&s._$AB.nextSibling,i),e.length=i)}_$AR(t=this._$AA.nextSibling,e){for(this._$AP?.(!1,!0,e);t!==this._$AB;){let s=$t(t).nextSibling;$t(t).remove(),t=s}}setConnected(t){this._$AM===void 0&&(this._$Cv=t,this._$AP?.(t))}},k=class{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(t,e,s,i,n){this.type=1,this._$AH=c,this._$AN=void 0,this.element=t,this.name=e,this._$AM=i,this.options=n,s.length>2||s[0]!==""||s[1]!==""?(this._$AH=Array(s.length-1).fill(new String),this.strings=s):this._$AH=c}_$AI(t,e=this,s,i){let n=this.strings,o=!1;if(n===void 0)t=R(this,t,e,0),o=!j(t)||t!==this._$AH&&t!==E,o&&(this._$AH=t);else{let l=t,a,d;for(t=n[0],a=0;a<n.length-1;a++)d=R(this,l[s+a],e,a),d===E&&(d=this._$AH[a]),o||=!j(d)||d!==this._$AH[a],d===c?t=c:t!==c&&(t+=(d??"")+n[a+1]),this._$AH[a]=d}o&&!i&&this.j(t)}j(t){t===c?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,t??"")}},rt=class extends k{constructor(){super(...arguments),this.type=3}j(t){this.element[this.name]=t===c?void 0:t}},nt=class extends k{constructor(){super(...arguments),this.type=4}j(t){this.element.toggleAttribute(this.name,!!t&&t!==c)}},ot=class extends k{constructor(t,e,s,i,n){super(t,e,s,i,n),this.type=5}_$AI(t,e=this){if((t=R(this,t,e,0)??c)===E)return;let s=this._$AH,i=t===c&&s!==c||t.capture!==s.capture||t.once!==s.once||t.passive!==s.passive,n=t!==c&&(s===c||i);i&&this.element.removeEventListener(this.name,this,s),n&&this.element.addEventListener(this.name,this,t),this._$AH=t}handleEvent(t){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,t):this._$AH.handleEvent(t)}},at=class{constructor(t,e,s){this.element=t,this.type=6,this._$AN=void 0,this._$AM=e,this.options=s}get _$AU(){return this._$AM._$AU}_$AI(t){R(this,t)}};var Kt=lt.litHtmlPolyfillSupport;Kt?.(D,I),(lt.litHtmlVersions??=[]).push("3.3.3");var Ot=(r,t,e)=>{let s=e?.renderBefore??t,i=s._$litPart$;if(i===void 0){let n=e?.renderBefore??null;s._$litPart$=i=new I(t.insertBefore(z(),n),n,void 0,e??{})}return i._$AI(r),i};var pt=globalThis,m=class extends y{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){let t=super.createRenderRoot();return this.renderOptions.renderBefore??=t.firstChild,t}update(t){let e=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(t),this._$Do=Ot(e,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return E}};m._$litElement$=!0,m.finalized=!0,pt.litElementHydrateSupport?.({LitElement:m});var Jt=pt.litElementPolyfillSupport;Jt?.({LitElement:m});(pt.litElementVersions??=[]).push("4.2.2");var J=r=>(t,e)=>{e!==void 0?e.addInitializer(()=>{customElements.define(r,t)}):customElements.define(r,t)};var Gt={attribute:!0,type:String,converter:L,reflect:!1,hasChanged:W},Yt=(r=Gt,t,e)=>{let{kind:s,metadata:i}=e,n=globalThis.litPropertyMetadata.get(i);if(n===void 0&&globalThis.litPropertyMetadata.set(i,n=new Map),s==="setter"&&((r=Object.create(r)).wrapped=!0),n.set(e.name,r),s==="accessor"){let{name:o}=e;return{set(l){let a=t.get.call(this);t.set.call(this,l),this.requestUpdate(o,a,r,!0,l)},init(l){return l!==void 0&&this.C(o,void 0,r,l),l}}}if(s==="setter"){let{name:o}=e;return function(l){let a=this[o];t.call(this,l),this.requestUpdate(o,a,r,!0,l)}}throw Error("Unsupported decorator location: "+s)};function N(r){return(t,e)=>typeof e=="object"?Yt(r,t,e):((s,i,n)=>{let o=i.hasOwnProperty(n);return i.constructor.createProperty(n,s),o?Object.getOwnPropertyDescriptor(i,n):void 0})(r,t,e)}function G(r){return N({...r,state:!0,attribute:!1})}var O="goe_steve";function ut(r){let t=new Map;for(let e of Object.values(r.entities))if(!(e.platform!==O||!e.device_id)&&!t.has(e.device_id)){let s=r.devices[e.device_id];t.set(e.device_id,s?.name_by_user||s?.name||e.device_id)}return[...t.entries()].map(([e,s])=>({id:e,name:s}))}function Mt(r,t){let e={tag_energy:[]};if(!t){let n=ut(r);n.length===1&&(t=n[0].id)}if(e.deviceId=t,!t)return e;let s=Object.values(r.entities).filter(n=>n.platform===O&&n.device_id===t),i=n=>{let o=s.find(a=>a.translation_key===n);return o?o.entity_id:s.find(a=>{let d=a.entity_id.split(".")[1]??"";return d===n||d.endsWith(`_${n}`)})?.entity_id};return e.status=i("status"),e.power_flow=i("power_flow"),e.surplus=i("surplus_for_car"),e.target_current=i("target_current"),e.controlling=i("controlling"),e.charging_mode=i("charging_mode"),e.battery_policy=i("battery_policy"),e.smart_control=i("smart_control"),e.auto_phase=i("auto_phase"),e.active_transaction=i("active_transaction"),e.last_session_energy=i("last_session_energy"),e.tag_energy=s.filter(n=>n.translation_key==="tag_energy"||n.entity_id.split(".")[1]?.includes("_tag_energy_")).map(n=>n.entity_id).sort(),e}var gt={"card.no_device":"No {name} device found. Set one up first, then add this card.","card.default_title":"Smart Charging","flow.solar":"Solar","flow.grid":"Grid","flow.export":"Export","flow.battery":"Battery","flow.home":"Home","flow.car":"Car","flow.no_car":"No car","control.mode":"Mode","control.battery":"Battery","control.smart_control":"Smart control","session.none":"No active session","session.charging":"Charging: {state}","session.last":"Last session: {energy}","session.blocked":"blocked","session.tag":"tag","editor.device":"Smart Charging device (optional \u2014 auto-detected)","editor.title":"Title (optional)","editor.show_flow":"Show energy flow","editor.show_controls":"Show controls","editor.show_sessions":"Show sessions & RFID"},Zt={"card.no_device":"Kein {name}-Ger\xE4t gefunden. Richte zuerst eines ein und f\xFCge dann diese Karte hinzu.","card.default_title":"Intelligentes Laden","flow.solar":"Solar","flow.grid":"Netz","flow.export":"Einspeisung","flow.battery":"Batterie","flow.home":"Haus","flow.car":"Auto","flow.no_car":"Kein Auto","control.mode":"Modus","control.battery":"Batterie","control.smart_control":"Intelligente Steuerung","session.none":"Kein aktiver Ladevorgang","session.charging":"L\xE4dt: {state}","session.last":"Letzter Ladevorgang: {energy}","session.blocked":"gesperrt","session.tag":"Tag","editor.device":"Smart-Charging-Ger\xE4t (optional \u2014 automatisch erkannt)","editor.title":"Titel (optional)","editor.show_flow":"Energiefluss anzeigen","editor.show_controls":"Steuerung anzeigen","editor.show_sessions":"Ladevorg\xE4nge & RFID anzeigen"},Qt={en:gt,de:Zt};function Xt(r){let t=(r?.locale?.language||r?.language||"en").toLowerCase().split("-")[0];return Qt[t]??gt}function b(r,t,e={}){let i=Xt(r)[t]??gt[t]??t;for(let[n,o]of Object.entries(e))i=i.replace(`{${n}}`,o);return i}var S=class extends m{constructor(){super(...arguments);this._schema=[{name:"device",selector:{device:{integration:O}}},{name:"title",selector:{text:{}}},{type:"grid",name:"",schema:[{name:"show_flow",selector:{boolean:{}}},{name:"show_controls",selector:{boolean:{}}},{name:"show_sessions",selector:{boolean:{}}}]}];this._label=e=>{switch(e.name){case"device":return b(this.hass,"editor.device");case"title":return b(this.hass,"editor.title");case"show_flow":return b(this.hass,"editor.show_flow");case"show_controls":return b(this.hass,"editor.show_controls");case"show_sessions":return b(this.hass,"editor.show_sessions");default:return e.name}}}setConfig(e){this._config=e}render(){return!this.hass||!this._config?c:p`<ha-form
      .hass=${this.hass}
      .data=${this._config}
      .schema=${this._schema}
      .computeLabel=${this._label}
      @value-changed=${this._valueChanged}
    ></ha-form>`}_valueChanged(e){let s={...e.detail.value};this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:s},bubbles:!0,composed:!0}))}};S.styles=P`
    ha-form {
      display: block;
      padding: 8px 0;
    }
  `,v([N({attribute:!1})],S.prototype,"hass",2),v([G()],S.prototype,"_config",2),S=v([J("goe-steve-card-editor")],S);var te="go-e + SteVe Smart Charging",q=r=>{if(r==null||Number.isNaN(r))return"\u2014";let t=Math.abs(r);return t>=1e3?`${(r/1e3).toFixed(t>=1e4?0:1)} kW`:`${Math.round(r)} W`},C=class extends m{static getConfigElement(){return document.createElement("goe-steve-card-editor")}static getStubConfig(t){return{type:"custom:goe-steve-card",device:ut(t)[0]?.id}}setConfig(t){this._config={show_flow:!0,show_controls:!0,show_sessions:!0,...t}}getCardSize(){return 8}get _entities(){return this.hass?Mt(this.hass,this._config?.device):null}_t(t,e={}){return b(this.hass,t,e)}render(){if(!this.hass||!this._config)return c;let t=this._entities;if(!t||!t.deviceId)return p`<ha-card>
        <div class="empty">
          <ha-icon icon="mdi:ev-station"></ha-icon>
          <p>${this._renderNoDevice()}</p>
        </div>
      </ha-card>`;let e=this._config.title??this._deviceName(t.deviceId)??this._t("card.default_title");return p`<ha-card>
      ${this._renderHeader(t,e)}
      <div class="content">
        ${this._config.show_flow?this._renderFlow(t):c}
        ${this._config.show_controls?this._renderControls(t):c}
        ${this._config.show_sessions?this._renderSessions(t):c}
      </div>
    </ha-card>`}_renderNoDevice(){let[t,e]=this._t("card.no_device").split("{name}");return p`${t}<b>${te}</b>${e??""}`}_renderHeader(t,e){let s=this._stateObj(t.status),i=s?.state&&s.state!=="unknown"?s.state:"\u2014",n=this._isOn(t.controlling),o=this._displayState(t.charging_mode),l=this._displayState(t.battery_policy);return p`<div class="header">
      <div class="title-row">
        <ha-icon class="brain ${n?"active":""}" icon="mdi:brain"></ha-icon>
        <span class="title">${e}</span>
      </div>
      <div class="reason">${i}</div>
      <div class="chips">
        ${o?p`<span class="chip"><ha-icon icon="mdi:ev-station"></ha-icon>${o}</span>`:c}
        ${l?p`<span class="chip"><ha-icon icon="mdi:home-battery"></ha-icon>${l}</span>`:c}
      </div>
    </div>`}_renderFlow(t){let e=this._stateObj(t.power_flow),s=e?.attributes??{},i=Number(s.pv_w??NaN),n=Number(s.grid_w??NaN),o=s.battery_w===null||s.battery_w===void 0?null:Number(s.battery_w),l=Number(s.car_w??(e?e.state:NaN)),a=Number(s.house_w??NaN),d=s.battery_soc,u=s.car_connected,h=50,g=(_,M,Z,Q,X,Ht="")=>dt`
      <g class="node" transform="translate(${_},${M})">
        <circle r="26"></circle>
        <foreignObject x="-13" y="-20" width="26" height="26">
          <ha-icon icon="${Z}"></ha-icon>
        </foreignObject>
        <text class="node-val" y="14">${X}</text>
        <text class="node-lbl" y="42">${Q}${Ht}</text>
      </g>`,f=(_,M,Z,Q)=>{let X=M?Math.max(.6,3-Math.min(Q,9e3)/3e3):0;return dt`
        <path class="edge" d="${_}"></path>
        <path
          class="edge-flow ${M?"active":""} ${Z?"rev":""}"
          d="${_}"
          style="${M?`animation-duration:${X}s`:""}"
        ></path>`};return p`<div class="flow">
      <svg viewBox="0 0 320 320" preserveAspectRatio="xMidYMid meet">
        ${f("M160,66 L160,134",i>h,!1,i)}
        ${f("M76,160 L134,160",Number.isNaN(n)?!1:Math.abs(n)>h,n<0,Math.abs(n))}
        ${o!==null?f("M244,160 L186,160",Math.abs(o)>h,o>0,Math.abs(o)):c}
        ${f("M160,186 L160,244",l>h,!1,l)}

        ${g(160,40,"mdi:solar-power",this._t("flow.solar"),q(i))}
        ${g(40,160,"mdi:transmission-tower",n<0?this._t("flow.export"):this._t("flow.grid"),q(Math.abs(n)))}
        ${o!==null?g(280,160,"mdi:home-battery",this._t("flow.battery"),q(Math.abs(o)),d!=null?` ${Math.round(Number(d))}%`:""):c}
        ${g(160,160,"mdi:home",this._t("flow.home"),q(a))}
        ${g(160,280,u===!1?"mdi:car-off":"mdi:car-electric",u===!1?this._t("flow.no_car"):this._t("flow.car"),q(l))}
      </svg>
    </div>`}_renderControls(t){let e=this._stateObj(t.charging_mode),s=this._stateObj(t.battery_policy),i=this._stateObj(t.smart_control);return p`<div class="controls">
      ${e?p`<div class="control">
            <span class="ctl-label">${this._t("control.mode")}</span>
            ${this._renderSelect(e)}
          </div>`:c}
      ${s?p`<div class="control">
            <span class="ctl-label">${this._t("control.battery")}</span>
            ${this._renderSelect(s)}
          </div>`:c}
      ${i?p`<div class="control">
            <span class="ctl-label">${this._t("control.smart_control")}</span>
            <ha-switch
              .checked=${this._isOn(t.smart_control)}
              @change=${n=>this._toggle(t.smart_control,n)}
            ></ha-switch>
          </div>`:c}
    </div>`}_renderSelect(t){let e=t.attributes.options??[];return p`<select
      class="ctl-select"
      @change=${s=>this._selectOption(t,s.target.value)}
    >
      ${e.map(s=>p`<option .value=${s} ?selected=${s===t.state}>
            ${this._localizeOption(t,s)}
          </option>`)}
    </select>`}_renderSessions(t){let e=this._stateObj(t.active_transaction),s=this._stateObj(t.last_session_energy),i=t.tag_energy.map(n=>this._stateObj(n)).filter(n=>!!n);return!e&&!s&&i.length===0?c:p`<div class="sessions">
      ${e?p`<div class="session-row">
            <ha-icon icon="mdi:card-account-details"></ha-icon>
            <span>${e.state==="idle"?this._t("session.none"):this._t("session.charging",{state:e.attributes.name??e.state})}</span>
          </div>`:c}
      ${s&&s.state&&s.state!=="unknown"?p`<div class="session-row">
            <ha-icon icon="mdi:history"></ha-icon>
            <span>${this._t("session.last",{energy:this._fmtState(s)})}</span>
          </div>`:c}
      ${i.length?p`<div class="tags">
            ${i.map(n=>p`<div class="tag">
                <span class="tag-id">${n.attributes.name??n.attributes.id_tag??this._t("session.tag")}</span>
                <span class="tag-kwh ${n.attributes.blocked?"blocked":""}">
                  ${this._fmtState(n)}${n.attributes.blocked?` \xB7 ${this._t("session.blocked")}`:""}
                </span>
              </div>`)}
          </div>`:c}
    </div>`}_stateObj(t){return t?this.hass.states[t]:void 0}_isOn(t){return this._stateObj(t)?.state==="on"}_displayState(t){let e=this._stateObj(t);return e?this._fmtState(e):null}_fmtState(t){return this.hass.formatEntityState?this.hass.formatEntityState(t):t.state}_localizeOption(t,e){let s=this.hass.entities?.[t.entity_id]?.translation_key;if(s){let i=`component.${O}.entity.select.${s}.state.${e}`,n=this.hass.localize?.(i);if(n)return n}if(this.hass.formatEntityState){let i=this.hass.formatEntityState({...t,state:e},e);if(i)return i}return e}_deviceName(t){let e=this.hass.devices[t];return e?.name_by_user||e?.name||null}_selectOption(t,e){e!==t.state&&this.hass.callService("select","select_option",{entity_id:t.entity_id,option:e})}_toggle(t,e){if(!t)return;let s=e.target.checked;this.hass.callService("switch",s?"turn_on":"turn_off",{entity_id:t})}};C.styles=P`
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
      max-height: 320px;
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
  `,v([N({attribute:!1})],C.prototype,"hass",2),v([G()],C.prototype,"_config",2),C=v([J("goe-steve-card")],C);window.customCards=window.customCards||[];window.customCards.push({type:"goe-steve-card",name:"go-e + SteVe Smart Charging",description:"Live energy flow, charging mode & battery policy with the brain's reasoning, inline controls and per-RFID energy.",preview:!0,documentationURL:"https://github.com/JustChr/HAgoe_steve"});export{C as GoeSteveCard};
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
